import unittest

from filip.cb.client import ContextBrokerClient
from filip.cb.models import \
    ActionType,\
    ContextMetadata, \
    ContextAttribute, \
    ContextEntity, \
    create_context_entity_model, \
    NamedContextMetadata, \
    Subscription, \
    Update
from filip.core.models import FiwareHeader


class TestModels(unittest.TestCase):
    def setUp(self) -> None:
        self.attr = {'temperature': {'value': 20,
                                     'type': 'Number'}}
        self.relation = {'relation': {'value': 'OtherEntity',
                                      'type': 'Relationship'}}
        self.entity_data = {'id': 'MyId',
                            'type': 'MyType'}
        self.entity_data.update(self.attr)
        self.entity_data.update(self.relation)

    def test_cb_attribute(self):
        attr = ContextAttribute(**{'value': 20, 'type': 'Text'})
        self.assertIsInstance(attr.value, str)
        attr = ContextAttribute(**{'value': 20, 'type': 'Number'})
        self.assertIsInstance(attr.value, float)
        attr = ContextAttribute(**{'value': [20, 20], 'type': 'Float'})
        self.assertIsInstance(attr.value, list)
        attr = ContextAttribute(**{'value': [20.0, 20.0], 'type': 'Integer'})
        self.assertIsInstance(attr.value, list)
        attr = ContextAttribute(**{'value': [20, 20], 'type': 'Array'})
        self.assertIsInstance(attr.value, list)

    def test_cb_metadata(self):
        md1 = ContextMetadata(type='Text', value='test')
        md2 = NamedContextMetadata(name='info', type='Text', value='test')
        md3 = [NamedContextMetadata(name='info', type='Text', value='test')]
        attr1 = ContextAttribute(value=20,
                                 type='Integer',
                                 metadata={'info': md1})
        attr2 = ContextAttribute(**attr1.dict(exclude={'metadata'}),
                                 metadata=md2)
        attr3 = ContextAttribute(**attr1.dict(exclude={'metadata'}),
                                 metadata=md3)
        self.assertEqual(attr1, attr2)
        self.assertEqual(attr1, attr3)

    def test_cb_entity(self):
        entity = ContextEntity(**self.entity_data)
        self.assertEqual(self.entity_data, entity.dict(exclude_unset=True))
        entity = ContextEntity.parse_obj(self.entity_data)
        self.assertEqual(self.entity_data, entity.dict(exclude_unset=True))
        properties = entity.get_properties()
        self.assertEqual(self.attr, {properties[0].name: properties[0].dict(
            exclude={'name', 'metadata'}, exclude_unset=True)})
        relations = entity.get_relationships()
        self.assertEqual(self.relation, {relations[0].name: relations[0].dict(
            exclude={'name', 'metadata'}, exclude_unset=True)})
        new_attr = {'new_attr': ContextAttribute(type='Number', value=25)}
        entity.add_properties(new_attr)
        generated_model = create_context_entity_model(data=self.entity_data)
        entity = generated_model(**self.entity_data)
        self.assertEqual(self.entity_data, entity.dict(exclude_unset=True))
        entity = generated_model.parse_obj(self.entity_data)
        self.assertEqual(self.entity_data, entity.dict(exclude_unset=True))

    def test_cb_subscriptions(self):
        sub_dict = {
            "description": "One subscription to rule them all",
            "subject": {
                "entities": [
                    {
                        "idPattern": ".*",
                        "type": "Room"
                    }
                ],
                "condition": {
                    "attrs": [
                        "temperature"
                    ],
                    "expression": {
                        "q": "temperature>40"
                    }
                }
            },
            "notification": {
                "http": {
                    "url": "http://localhost:1234"
                },
                "attrs": [
                    "temperature",
                    "humidity"
                ]
            },
            "expires": "2016-04-05T14:00:00Z",
            "throttling": 5
        }

        sub = Subscription.parse_obj(sub_dict)
        fiware_header = FiwareHeader(service='filip',
                                     service_path='/testing')
        with ContextBrokerClient(fiware_header=fiware_header) as client:
            sub_id = client.post_subscription(subscription=sub)
            sub_res = client.get_subscription(subscription_id=sub_id)
            self.assertEqual(sub.json(exclude={'id', 'status', 'expires'},
                                      exclude_none=True),
                             sub_res.json(exclude={'id', 'status', 'expires'},
                                          exclude_none=True))
            sub_ids = [sub.id for sub in client.get_subscription_list()]
            for sub_id in sub_ids:
                client.delete_subscription(subscription_id=sub_id)

    def test_update_model(self):
        entities = [ContextEntity(id='1', type='myType')]
        action_type = ActionType.APPEND
        Update(actionType=action_type, entities=entities)
        with self.assertRaises(ValueError):
            Update(actionType='test', entities=entities)