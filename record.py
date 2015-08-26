import abc
import copy
import types
import collections

# This is a token used symbolically below
Required = object()


class DataError(Exception):
    """
    Represents an error encountered while initializing a mutable data type.
    """
    pass


class Validator(object):
    """
    An abstract base class for field validators.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, default):
        """
        Initialize the validator with a default value
        """
        self.default = default

    @abc.abstractmethod
    def validate(self, value, field_name):
        """
        Base classes should override this method and raise an exception if the value is invalid
        for the given field.
        """
        pass


class MustSatisfy(Validator):
    """
    Represents a custom validator for members of a mutable data type.
    """

    def __init__(self, predicate, default=Required):
        super(MustSatisfy, self).__init__(default)
        self._predicate = predicate

    def validate(self, value, field_name):
        if not self._predicate(value):
            raise DataError('%s failed validation (value was %s)' % (field_name, value))


class InstanceOf(Validator):
    """
    Requires that a member be an instance of a particular class.
    """
    def __init__(self, type, default=Required):
        super(InstanceOf, self).__init__(default)
        self._type = type

    def validate(self, value, field_name):
        if not isinstance(value, self._type):
            raise DataError('%s is not an instance of %s' % (field_name, value))


class InstanceOrNone(Validator):
    """
    Requires that a member be an instance of a particular class, or None.
    """
    def __init__(self, type, default=None):
        super(InstanceOrNone, self).__init__(default)
        self._type = type

    def validate(self, value, field_name):
        if value is not None and not isinstance(value, self._type):
            raise DataError('%s is not an instance of %s' % (field_name, value))


class OneOf(Validator):
    """
    Requires that a member be one of a pre-set range of values.
    """
    def __init__(self, *possible_values, default=None):
        super(OneOf, self).__init__(default)
        self._possible_values = possible_values

    def validate(self, value, field_name):
        if value is None and self.default is not None:
            # No value was given, and a default was supplied
            return
        if value not in self._possible_values:
            raise DataError('%s is not a valid value for %s' % (value, field_name))


class Length(Validator):
    """
    Requires that a member have a certain length
    """
    def __init__(self, n, default=None):
        super(Length, self).__init__(default)
        self._n = n

    def validate(self, value, field_name):
        if value is None and self.default is not None:
            # No value was given, and a default was supplied
            return
        try:
            if len(value) != self._n:
                raise DataError('%s has length %d but expected %d' % (value, len(value), self._n))
        except TypeError:
            raise DataError('%s has no length so is not a valid value for %s' % (value, field_name))


class MutableRecord(object):
    """
    Base class for all types created by make_mutable_type.
    """
    def __init__(self, **kwargs):
        self._members = type(self).members
        for key, spec in self._members.items():
            # Resolve validator and default value
            if isinstance(spec, Validator):
                validator = spec
                default = validator.default
            else:
                validator = None
                default = spec

            # Check for missing required args
            if key not in kwargs and default is Required:
                raise DataError('%s is required' % key)

            # Resolve value for this member
            if key in kwargs:
                value = kwargs[key]
            else:
                value = copy.deepcopy(default)

            # Run validator
            if validator is not None:
                validator.validate(value, key)

            # Store
            setattr(self, key, value)

        # Check for invalid keyword arguments
        for key in kwargs.keys():
            if key not in self._members:
                raise DataError('%s is not a member of %s' % (key, type(self).__name__))

    def __str__(self):
        """
        Get a string representation of this object.
        """
        fields = ', '.join('%s=%s' % (k, getattr(self, k)) for k in self._members.keys())
        return '%s(%s)' % (type(self).__name__, fields)

    def __repr__(self):
        """
        Get a string representation of this object.
        """
        return str(self)


class MutableRecordSet(list):
    """
    Base class for all types created by make_mutable_list_type.
    """
    def __init__(self, *args):
        assert 0 <= len(args) <= 1
        super(MutableRecordSet, self).__init__()
        if len(args) > 0:
            for object in args[0]:
                self.append(object)

    def __getitem__(self, index):
        value = super(MutableRecordSet, self).__getitem__(index)
        if isinstance(index, slice):
            return type(self)(value)
        else:
            return value

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            objects = list(value)  # make a copy so that we don't throw any away
            for object in objects:
                assert isinstance(object, self.value_type)
            super(MutableRecordSet, self).__setitem__(index, objects)
        else:
            assert isinstance(value, self.value_type)
            super(MutableRecordSet, self).__setitem__(index, value)

    def __getslice__(self, start, end):
        # only used in python 2
        return type(self)(super(MutableRecordSet, self).__getslice__(start, end))

    def __setslice__(self, start, end, iterable):
        # only used in python 2
        objects = list(iterable)  # make a copy so that we don't throw any away
        for object in objects:
            assert isinstance(object, self.value_type)
        type(self)(super(MutableRecordSet, self).__setitem__(start, end, objects))

    def append(self, object):
        assert isinstance(object, self.value_type)
        super(MutableRecordSet, self).append(object)

    def extend(self, iterable):
        for object in iterable:
            assert isinstance(object, self.value_type)
            self.append(object)  # now that we've popped the item off the iterator we must use it

    def insert(self, index, object):
        assert isinstance(object, self.value_type)
        super(MutableRecordSet, self).insert(index, object)

    def append_new(self, **kwargs):
        self.append(self.value_type(**kwargs))

    def insert_new(self, index, **kwargs):
        self.insert(index, self.value_type(**kwargs))

    def __str__(self):
        return '[' + '\n '.join(map(str, self)) + ']'

    def __repr__(self):
        return '[' + ',\n '.join(map(repr, self)) + ']'


class FieldView(object):
    """
    Represents a view of one field of a MutableDataList subclass.
    """
    def __init__(self, container, field):
        self._container = container
        self._field = field

    def __len__(self):
        return len(self._container)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return FieldView(self._container[index], self._field)
        else:
            return getattr(self._container[index], self._field)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            for item, entry in zip(self._container[index], value):
                setattr(item, self._field, entry)
        else:
            setattr(self._container[index], self._field, value)

    def __iter__(self):
        for item in self._container:
            yield getattr(item, self._field)

    def __str__(self):
        return '[' + ', '.join(map(repr, self)) + ']'

    def __repr__(self):
        return str(self)


class FieldViewDescriptor(object):
    """
    A descriptor that resolves to a FieldView for a specific field.
    """
    def __init__(self, field):
        self._field = field

    def __get__(self, instance, type=None):
        return FieldView(instance, self._field)


def make_mutable_type(typename, **members):
    """
    Construct a type with mutable members.
    """
    return MutableRecordType.__new__(MutableRecordType, typename, (object,), members)


def make_mutable_list_type(typename, value_type, **members):
    """
    Construct a type with mutable members.
    """
    bases = (MutableRecordSet,)
    namespace = {'value_type': value_type}
    for key in members.keys():
        namespace[key+'s'] = FieldViewDescriptor(key)
    return type(typename, bases, namespace)


class MutableRecordType(type):
    """
    A metaclass for constructing mutable record types.
    """
    @classmethod
    def __prepare__(metacls, name, bases): 
        return collections.OrderedDict()

    def __new__(mcl, name, bases, clsdict):
        if any(base is not object for base in bases):
            raise TypeError("MutableRecord types may not be have any base class (base was %s)" % base.__name__)

        bases = (MutableRecord,)
        namespace = {}
        fields = collections.OrderedDict()

        # Separate the dictionary into functions and nonfunctions
        for key, val in clsdict.items():
            if key.startswith("__") or isinstance(val, (types.FunctionType, type, classmethod, property)):
                namespace[key] = val
            else:
                fields[key] = val

        namespace['__slots__'] = fields.keys()

        result_type = super(MutableRecordType, mcl).__new__(mcl, name, bases, namespace)
        result_type.List = make_mutable_list_type(name+'List', result_type, **fields)
        result_type.members = fields
        return result_type
