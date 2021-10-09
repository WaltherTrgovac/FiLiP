"""
@author Thomas Storek

Tests for time series api client aka QuantumLeap
"""
import logging
import unittest
from random import random

import requests
import time
from filip.clients.ngsi_v2 import \
    ContextBrokerClient, \
    QuantumLeapClient
from filip.models.base import FiwareHeader
from filip.models.ngsi_v2.context import ContextEntity
from filip.models.ngsi_v2.subscriptions import Message
from filip.utils.cleanup import clean_test, clear_all
from tests.config import settings


logger = logging.getLogger(__name__)


class TestTimeSeries(unittest.TestCase):
    """
    Test class for time series api client
    """
    def setUp(self) -> None:
        """
        Setup test data
        Returns:
            None
        """
        self.fiware_header = FiwareHeader(
            service=settings.FIWARE_SERVICE,
            service_path=settings.FIWARE_SERVICEPATH)
        self.ql_client = QuantumLeapClient(
            url=settings.QL_URL,
            fiware_header=self.fiware_header)

        self.cb_client = ContextBrokerClient(
            url=settings.CB_URL,
            fiware_header=self.fiware_header)

    def __create_entities(self):
        def create_attr():
            return {'temperature': {'value': random(),
                                         'type': 'Number'},
                    'humidity': {'value': random(),
                                 'type': 'Number'},
                    'co2': {'value': random(),
                            'type': 'Number'}}
        return [ContextEntity(id='Kitchen', type='Room', **create_attr()),
                ContextEntity(id='LivingRoom', type='Room', **create_attr())]

    def test_meta_endpoints(self) -> None:
        """
        Test meta data endpoints
        Returns:
            None
        """
        with QuantumLeapClient(
                url=settings.QL_URL,
                fiware_header=self.fiware_header) \
                as client:
            self.assertIsNotNone(client.get_version())
            self.assertIsNotNone(client.get_health())

    @clean_test(fiware_service=settings.FIWARE_SERVICE,
                fiware_servicepath=settings.FIWARE_SERVICEPATH,
                cb_url=settings.CB_URL,
                ql_url=settings.QL_URL)
    def test_input_endpoints(self) -> None:
        """
        Test input endpoint
        Returns:
            None
        """
        entities = self.__create_entities()
        for entity in entities:
            self.cb_client.post_entity(entity)

        with QuantumLeapClient(
                url=settings.QL_URL,
                fiware_header=self.fiware_header) \
                as client:

            notification_message = Message(data=entities,
                                           subscriptionId="test")
            client.post_subscription(entity_id=entities[0].id)
            client.post_notification(notification_message)

    @clean_test(fiware_service=settings.FIWARE_SERVICE,
                fiware_servicepath=settings.FIWARE_SERVICEPATH,
                ql_url=settings.QL_URL)
    def test_entity_context(self) -> None:
        """
        Test entities endpoint
        Returns:
            None
        """
        entities = self.__create_entities()

        with QuantumLeapClient(
                url=settings.QL_URL,
                fiware_header=self.fiware_header) \
                as client:

            notification_message = Message(data=entities,
                                           subscriptionId="test")
            client.post_notification(notification_message)

            time.sleep(1)
            entities = client.get_entities(entity_type=entities[0].type)
            for entity in entities:
                logger.info(entity.json(indent=2))

    @clean_test(fiware_service=settings.FIWARE_SERVICE,
                fiware_servicepath=settings.FIWARE_SERVICEPATH,
                ql_url=settings.QL_URL,
                )
    def test_query_endpoints(self) -> None:
        """
        Test queries
        Returns:
            None
        """
        with QuantumLeapClient(url=settings.QL_URL,
                               fiware_header=self.fiware_header) \
                as client:

            for i in range(10):
                entities = self.__create_entities()
                notification_message = Message(data=entities,
                                               subscriptionId="test")
                client.post_notification(notification_message)

            time.sleep(0.5)
            with self.assertRaises(requests.RequestException):
                client.get_entity_by_id(entity_id=entities[0].id,
                                        entity_type='MyType')
            for entity in entities:
                # get by id
                attrs_id = client.get_entity_by_id(entity_id=entities[0].id,
                                                   aggr_period='minute',
                                                   aggr_method='avg',
                                                   attrs='temperature,co2')
                logger.info(attrs_id.json(indent=2))
                logger.info(attrs_id.to_pandas())

                attrs_values_id = client.get_entity_values_by_id(
                    entity_id=entity.id)
                logger.info(attrs_values_id.to_pandas())

                attr_id = client.get_entity_attr_by_id(
                    entity_id=entity.id, attr_name="temperature")
                logger.info(attr_id.to_pandas())

                attr_values_id = client.get_entity_attr_values_by_id(
                    entity_id=entity.id, attr_name="temperature")
                logger.info(attr_values_id.to_pandas())

                # get by type
                attrs_type = client.get_entity_by_type(
                    entity_type=entity.type)
                for entity_id in attrs_type:
                    logger.info(entity_id.to_pandas())

                attrs_values_type = client.get_entity_values_by_type(
                     entity_type=entity.type)
                for entity_id in attrs_values_type:
                    logger.info(entity_id.to_pandas())

                attr_type = client.get_entity_attr_by_type(
                    entity_type=entity.type, attr_name="temperature")
                for entity_id in attr_type:
                    logger.info(entity_id.to_pandas())

                attr_values_type = client.get_entity_attr_values_by_type(
                    entity_type=entity.type, attr_name="temperature")
                for entity_id in attr_values_type:
                    logger.info(entity_id.to_pandas())

    def tearDown(self) -> None:
        """
        Clean up server
        Returns:
            None
        """
        clear_all(fiware_header=self.fiware_header,
                  cb_url=settings.CB_URL,
                  ql_url=settings.QL_URL)

        self.ql_client.close()
        self.cb_client.close()
