"""
NGSI LD models for context broker interaction
"""
import logging
from typing import Any, List, Dict, Union, Optional

from aenum import Enum
from pydantic import field_validator, ConfigDict, BaseModel, Field
from filip.models.ngsi_v2 import ContextEntity
from filip.utils.validators import FiwareRegex, \
    validate_fiware_datatype_string_protect, validate_fiware_standard_regex


class DataTypeLD(str, Enum):
    """
    In NGSI-LD the data types on context entities are only divided into properties and relationships.
    """
    _init_ = 'value __doc__'

    PROPERTY = "Property", "All attributes that do not represent a relationship"
    RELATIONSHIP = "Relationship", "Reference to another context entity, which can be identified with a URN."


# NGSI-LD entity models
class ContextProperty(BaseModel):
    """
    The model for a property is represented by a JSON object with the following syntax:

    The attribute value is specified by the value, whose value can be any data type. This does not need to be
    specified further.

    The NGSI type of the attribute is fixed and does not need to be specified.
    Example:

        >>> data = {"value": <...>}

        >>> attr = ContextProperty(**data)

    """
    type: Optional[str] = Field(
        default="Property",
        title="type",
        frozen=True
    )
    value: Optional[Union[Union[float, int, bool, str, List, Dict[str, Any]],
                          List[Union[float, int, bool, str, List,
                                     Dict[str, Any]]]]] = Field(
        default=None,
        title="Property value",
        description="the actual data"
    )
    observedAt: Optional[str] = Field(
        None, titel="Timestamp",
        description="Representing a timestamp for the "
                    "incoming value of the property.",
        max_length=256,
        min_length=1,
    )
    field_validator("observedAt")(validate_fiware_datatype_string_protect)

    UnitCode: Optional[str] = Field(
        None, titel="Unit Code",
        description="Representing the unit of the value. "
                    "Should be part of the defined units "
                    "by the UN/ECE Recommendation No. 21"
                    "https://unece.org/fileadmin/DAM/cefact/recommendations/rec20/rec20_rev3_Annex2e.pdf ",
        max_length=256,
        min_length=1,
        # pattern=FiwareRegex.string_protect.value,  # Make it FIWARE-Safe
    )
    field_validator("UnitCode")(validate_fiware_datatype_string_protect)

    @field_validator("type")
    @classmethod
    def check_property_type(cls, value):
        """
        Force property type to be "Property"
        Args:
            value: value field
        Returns:
            value
        """
        if not value == "Property":
            logging.warning(msg='NGSI_LD Properties must have type "Property"')
        value = "Property"
        return value


class NamedContextProperty(ContextProperty):
    """
    Context properties are properties of context entities. For example, the current speed of a car could be modeled
    as the current_speed property of the car-104 entity.

    In the NGSI-LD data model, properties have a name, the type "property" and a value.
    """
    name: str = Field(
        titel="Property name",
        description="The property name describes what kind of property the "
                    "attribute value represents of the entity, for example "
                    "current_speed. Allowed characters "
                    "are the ones in the plain ASCII set, except the following "
                    "ones: control characters, whitespace, &, ?, / and #.",
        max_length=256,
        min_length=1,
        # pattern=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )
    field_validator("name")(validate_fiware_datatype_string_protect)


class ContextGeoPropertyValue(BaseModel):
    """
    The value for a Geo property is represented by a JSON object with the following syntax:

    A type with value "Point" and the
    coordinates with a list containing the coordinates as value

    Example:
        "value": {
            "type": "Point",
            "coordinates": [
                -3.80356167695194,
                43.46296641666926
            ]
        }
    }

    """
    type: Optional[str] = Field(
        default="Point",
        title="type",
        frozen=True
    )
    coordinates: List[float] = Field(
        default=None,
        title="Geo property coordinates",
        description="the actual coordinates"
    )
    @field_validator("type")
    @classmethod
    def check_geoproperty_value_type(cls, value):
        """
        Force property type to be "Point"
        Args:
            value: value field
        Returns:
            value
        """
        if not value == "Point":
            logging.warning(msg='NGSI_LD GeoProperty values must have type "Point"')
        value = "Point"
        return value

    @field_validator("coordinates")
    @classmethod
    def check_geoproperty_value_coordinates(cls, value):
        """
        Force property coordinates to be lis of two floats
        Args:
            value: value field
        Returns:
            value
        """
        if not isinstance(value, list) or len(value) != 2:
            logging.error(msg='NGSI_LD GeoProperty values must have coordinates as list with length two')
            raise ValueError
        for element in value:
            if not isinstance(element, float):
                logging.error(msg='NGSI_LD GeoProperty values must have coordinates as list of floats')
                raise TypeError
        return value


class ContextGeoProperty(BaseModel):
    """
    The model for a Geo property is represented by a JSON object with the following syntax:

    The attribute value is a JSON object with two contents.

    Example:

        "location": {
        "type": "GeoProperty",
        "value": {
            "type": "Point",
            "coordinates": [
                -3.80356167695194,
                43.46296641666926
            ]
        }
    }

    """
    type: Optional[str] = Field(
        default="GeoProperty",
        title="type",
        frozen=True
    )
    value: Optional[ContextGeoPropertyValue] = Field(
        default=None,
        title="GeoProperty value",
        description="the actual data"
    )

    @field_validator("type")
    @classmethod
    def check_geoproperty_type(cls, value):
        """
        Force property type to be "GeoProperty"
        Args:
            value: value field
        Returns:
            value
        """
        if not value == "GeoProperty":
            logging.warning(msg='NGSI_LD GeoProperties must have type "GeoProperty"')
        value = "GeoProperty"
        return value


class NamedContextGeoProperty(ContextProperty):
    """
    Context GeoProperties are geo properties of context entities. For example, the coordinates of a building .

    In the NGSI-LD data model, properties have a name, the type "Geoproperty" and a value.
    """
    name: str = Field(
        titel="Property name",
        description="The property name describes what kind of property the "
                    "attribute value represents of the entity, for example "
                    "current_speed. Allowed characters "
                    "are the ones in the plain ASCII set, except the following "
                    "ones: control characters, whitespace, &, ?, / and #.",
        max_length=256,
        min_length=1,
    )
    field_validator("name")(validate_fiware_datatype_string_protect)


class ContextRelationship(BaseModel):
    """
    The model for a relationship is represented by a JSON object with the following syntax:

    The attribute value is specified by the object, whose value can be a reference to another context entity. This
    should be specified as the URN. The existence of this entity is not assumed.

    The NGSI type of the attribute is fixed and does not need to be specified.

    Example:

        >>> data = {"object": <...>}

        >>> attr = ContextRelationship(**data)

    """
    type: Optional[str] = Field(
        default="Relationship",
        title="type",
        frozen=True
    )
    object: Optional[Union[Union[float, int, bool, str, List, Dict[str, Any]],
                           List[Union[float, int, bool, str, List,
                                      Dict[str, Any]]]]] = Field(
        default=None,
        title="Realtionship object",
        description="the actual object id"
    )

    @field_validator("type")
    @classmethod
    def check_relationship_type(cls, value):
        """
        Force property type to be "Relationship"
        Args:
            value: value field
        Returns:
            value
        """
        if not value == "Relationship":
            logging.warning(msg='NGSI_LD relationships must have type "Relationship"')
        value = "Relationship"
        return value


class NamedContextRelationship(ContextRelationship):
    """
    Context Relationship are relations of context entities to each other.
    For example, the current_speed of the entity car-104 could be modeled.
    The location could be modeled as located_in the entity Room-001.

    In the NGSI-LD data model, relationships have a name, the type "relationship" and an object.
    """
    name: str = Field(
        titel="Attribute name",
        description="The attribute name describes what kind of property the "
                    "attribute value represents of the entity, for example "
                    "current_speed. Allowed characters "
                    "are the ones in the plain ASCII set, except the following "
                    "ones: control characters, whitespace, &, ?, / and #.",
        max_length=256,
        min_length=1,
        # pattern=FiwareRegex.string_protect.value,
        # Make it FIWARE-Safe
    )
    field_validator("name")(validate_fiware_datatype_string_protect)


class ContextLDEntityKeyValues(BaseModel):
    """
    Base Model for an entity is represented by a JSON object with the following
    syntax.

    The entity id is specified by the object's id property, whose value
    is a string containing the entity id.

    The entity type is specified by the object's type property, whose value
    is a string containing the entity's type name.

    """
    id: str = Field(
        ...,
        title="Entity Id",
        description="Id of an entity in an NGSI context broker. Allowed "
                    "characters are the ones in the plain ASCII set, except "
                    "the following ones: control characters, "
                    "whitespace, &, ?, / and #."
                    "the id should be structured according to the urn naming scheme.",
        examples=['urn:ngsi-ld:Room:001'],
        max_length=256,
        min_length=1,
        # pattern=FiwareRegex.standard.value,  # Make it FIWARE-Safe
        frozen=True
    )
    field_validator("id")(validate_fiware_standard_regex)
    type: str = Field(
        ...,
        title="Entity Type",
        description="Id of an entity in an NGSI context broker. "
                    "Allowed characters are the ones in the plain ASCII set, "
                    "except the following ones: control characters, "
                    "whitespace, &, ?, / and #.",
        examples=["Room"],
        max_length=256,
        min_length=1,
        # pattern=FiwareRegex.standard.value,  # Make it FIWARE-Safe
        frozen=True
    )
    field_validator("type")(validate_fiware_standard_regex)
    context: List[str] = Field(
        ...,
        title="@context",
        description="providing an unambiguous definition by mapping terms to "
                    "URIs. For practicality reasons, "
                    "it is recommended to have a unique @context resource, "
                    "containing all terms, subject to be used in every "
                    "FIWARE Data Model, the same way as http://schema.org does.",
        examples=["[https://schema.lab.fiware.org/ld/context,"
                "https://uri.etsi.org/ngsi-ld/v1/ngsi-ld-core-context.jsonld]"],
        max_length=256,
        min_length=1,
        frozen=True
    )
    model_config = ConfigDict(extra='allow', validate_default=True,
                              validate_assignment=True)


class PropertyFormat(str, Enum):
    """
    Format to decide if properties of ContextEntity class are returned as
    List of NamedContextAttributes or as Dict of ContextAttributes.
    """
    LIST = 'list'
    DICT = 'dict'


class ContextLDEntity(ContextLDEntityKeyValues, ContextEntity):
    """
    Context LD entities, or simply entities, are the center of gravity in the
    FIWARE NGSI-LD information model. An entity represents a thing, i.e., any
    physical or logical object (e.g., a sensor, a person, a room, an issue in
    a ticketing system, etc.). Each entity has an entity id.
    Furthermore, the type system of FIWARE NGSI enables entities to have an
    entity type. Entity types are semantic types; they are intended to describe
    the type of thing represented by the entity. For example, a context
    entity #with id sensor-365 could have the type temperatureSensor.

    Each entity is uniquely identified by its id.

    The entity id is specified by the object's id property, whose value
    is a string containing the entity id.

    The entity type is specified by the object's type property, whose value
    is a string containing the entity's type name.

    Entity attributes are specified by additional properties and relationships, whose names are
    the name of the attribute and whose representation is described in the
    "ContextProperty"/"ContextRelationship"-model. Obviously, id and type are
    not allowed to be used as attribute names.

    Example:

        >>> data = {'id': 'MyId',
                    'type': 'MyType',
                    'my_attr': {'value': 20}}

        >>> entity = ContextLDEntity(**data)

    """

    def __init__(self,
                 id: str,
                 type: str,
                 **data):

        super().__init__(id=id, type=type, **data)
    model_config = ConfigDict(extra='allow', validate_default=True, validate_assignment=True)

    @field_validator("id")
    @classmethod
    def _validate_id(cls, id: str):
        if not id.startswith("urn:ngsi-ld:"):
            raise ValueError('Id has to be an URN and starts with "urn:ngsi-ld:"')
        return id

    @classmethod
    def _validate_properties(cls, data: Dict):
        attrs = {}
        for key, attr in data.items():
            if key not in ContextEntity.model_fields:
                if attr["type"] == DataTypeLD.RELATIONSHIP:
                    attrs[key] = ContextRelationship.model_validate(attr)
                else:
                    attrs[key] = ContextProperty.model_validate(attr)
        return attrs

    def get_properties(self,
                       response_format: Union[str, PropertyFormat] =
                       PropertyFormat.LIST) -> \
            Union[List[NamedContextProperty],
                  Dict[str, ContextProperty]]:
        """
        Args:
            response_format:

        Returns:

        """
        response_format = PropertyFormat(response_format)
        if response_format == PropertyFormat.DICT:
            return {key: ContextProperty(**value) for key, value in
                    self.model_dump().items() if key not in ContextLDEntity.model_fields
                    and value.get('type') != DataTypeLD.RELATIONSHIP}

        return [NamedContextProperty(name=key, **value) for key, value in
                self.model_dump().items() if key not in
                ContextLDEntity.model_fields and
                value.get('type') != DataTypeLD.RELATIONSHIP]

    def add_attributes(self, **kwargs):
        """
        Invalid in NGSI-LD
        """
        raise NotImplementedError(
            "This method should not be used in NGSI-LD")

    def get_attribute(self, **kwargs):
        """
        Invalid in NGSI-LD
        """
        raise NotImplementedError(
            "This method should not be used in NGSI-LD")

    def get_attributes(self, **kwargs):
        """
        Invalid in NGSI-LD
        """
        raise NotImplementedError(
            "This method should not be used in NGSI-LD")

    def delete_attributes(self, **kwargs):
        """
        Invalid in NGSI-LD
        """
        raise NotImplementedError(
            "This method should not be used in NGSI-LD")

    def delete_properties(self, props: Union[Dict[str, ContextProperty],
                                             List[NamedContextProperty],
                                             List[str]]):
        """
        Delete the given properties from the entity

        Args:
            props: can be given in multiple forms
                1) Dict: {"<property_name>": ContextProperty, ...}
                2) List: [NamedContextProperty, ...]
                3) List: ["<property_name>", ...]

        Returns:

        """
        names: List[str] = []
        if isinstance(props, list):
            for entry in props:
                if isinstance(entry, str):
                    names.append(entry)
                elif isinstance(entry, NamedContextProperty):
                    names.append(entry.name)
        else:
            names.extend(list(props.keys()))

        # check there are no relationships
        relationship_names = [rel.name for rel in self.get_relationships()]
        for name in names:
            if name in relationship_names:
                raise TypeError(f"{name} is a relationship")

        for name in names:
            delattr(self, name)

    def add_properties(self, attrs: Union[Dict[str, ContextProperty],
                                          List[NamedContextProperty]]) -> None:
        """
        Add property to entity
        Args:
            attrs:
        Returns:
            None
        """
        if isinstance(attrs, list):
            attrs = {attr.name: ContextProperty(**attr.dict(exclude={'name'}))
                     for attr in attrs}
        for key, attr in attrs.items():
            self.__setattr__(name=key, value=attr)

    def add_relationships(self, attrs: Union[Dict[str, ContextRelationship],
                                             List[NamedContextRelationship]]) -> None:
        """
        Add relationship to entity
        Args:
            attrs:
        Returns:
            None
        """
        if isinstance(attrs, list):
            attrs = {attr.name: ContextRelationship(**attr.dict(exclude={'name'}))
                     for attr in attrs}
        for key, attr in attrs.items():
            self.__setattr__(name=key, value=attr)

    def get_relationships(self,
                          response_format: Union[str, PropertyFormat] =
                          PropertyFormat.LIST) \
            -> Union[List[NamedContextRelationship],
                     Dict[str, ContextRelationship]]:
        """
        Get all relationships of the context entity

        Args:
            response_format:

        Returns:

        """
        response_format = PropertyFormat(response_format)
        if response_format == PropertyFormat.DICT:
            return {key: ContextRelationship(**value) for key, value in
                    self.model_dump().items() if key not in ContextLDEntity.model_fields
                    and value.get('type') == DataTypeLD.RELATIONSHIP}
        return [NamedContextRelationship(name=key, **value) for key, value in
                self.model_dump().items() if key not in
                ContextLDEntity.model_fields and
                value.get('type') == DataTypeLD.RELATIONSHIP]


class ActionTypeLD(str, Enum):
    """
    Options for queries
    """

    CREATE = "create"
    UPSERT = "upsert"
    UPDATE = "update"
    DELETE = "delete"


class UpdateLD(BaseModel):
    """
    Model for update action
    """
    entities: List[ContextEntity] = Field(
        description="an array of entities, each entity specified using the "
                    "JSON entity representation format "
    )