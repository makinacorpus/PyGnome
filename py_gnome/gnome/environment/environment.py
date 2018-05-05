"""
module contains objects that contain weather related data. For example,
the Wind object defines the Wind conditions for the spill
"""
import copy

from repoze.lru import lru_cache
from colander import SchemaNode, MappingSchema, Float, String, drop, OneOf

import gsw

import numpy as np

import unit_conversion as uc

from gnome import constants
from gnome.utilities import serializable
from gnome.utilities.time_utils import date_to_sec, sec_to_datetime
from gnome.persist import base_schema

from .. import _valid_units


class EnvironmentMeta(type):
    def __init__(cls, name, bases, dct):
        cls._subclasses = []
        for c in cls.__mro__:
            if hasattr(c, '_subclasses') and c is not cls:
                c._subclasses.append(cls)


class Environment(object):
    """
    A base class for all classes in environment module

    This is primarily to define a dtype such that the OrderedCollection
    defined in the Model object requires it.
    """

    _subclasses = []
    _state = copy.deepcopy(serializable.Serializable._state)

    # env objects referenced by others using this attribute name
    # eg: For Wind objects, set to 'wind', for Water object set to 'water'
    # so we have a way to identify all wind objects without relying on
    # insinstance() checks. Used by model to automatically hook up objects that
    # reference environment objects
    _ref_as = 'environment'

    __metaclass__ = EnvironmentMeta

    def __init__(self, name=None, make_default_refs=True):
        '''
        base class for environment objects

        :param name=None:
        '''
        if name is not None:
            self.name = name

        self.make_default_refs = make_default_refs

    def prepare_for_model_run(self, model_time):
        """
        Override this method if a derived environment class needs to perform
        any actions prior to a model run
        """
        pass

    def prepare_for_model_step(self, model_time):
        """
        Override this method if a derived environment class needs to perform
        any actions prior to a model run
        """
        pass

    def get_wind_speed(self, points, model_time,
                       coord_sys='r', fill_value=1.0):
        '''
        Wrapper for the weatherers so they can extrapolate
        '''
        retval = self.wind.at(points, model_time, coord_sys=coord_sys)

        if isinstance(retval, np.ma.MaskedArray):
            return retval.filled(fill_value)
        else:
            return retval

    def check_time(self, wind, model_time):
        '''
            Should have an option to extrapolate but for now we do by default

            TODO, FIXME: This function does not appear to be used by anything.
                         Removing it does not break any of the unit tests.
                         If it is not used, it should probably go away.
        '''
        new_model_time = model_time

        if wind is not None:
            if model_time is not None:
                timeval = date_to_sec(model_time)
                start_time = wind.get_start_time()
                end_time = wind.get_end_time()

                if end_time == start_time:
                    return model_time

                if timeval < start_time:
                    new_model_time = sec_to_datetime(start_time)

                if timeval > end_time:
                    new_model_time = sec_to_datetime(end_time)
            else:
                return model_time

        return new_model_time


# define valid units at module scope because the Schema and Object both use it
_valid_temp_units = _valid_units('Temperature')
_valid_dist_units = _valid_units('Length')
_valid_kvis_units = _valid_units('Kinematic Viscosity')
_valid_density_units = _valid_units('Density')
_valid_salinity_units = ('psu',)
_valid_sediment_units = _valid_units('Concentration In Water')


class UnitsSchema(MappingSchema):
    temperature = SchemaNode(String(),
                             description='SI units for temp',
                             validator=OneOf(_valid_temp_units))

    # for now salinity only has one units
    salinity = SchemaNode(String(),
                          description='SI units for salinity',
                          validator=OneOf(_valid_salinity_units))

    # sediment load units? Concentration In Water?
    sediment = SchemaNode(String(),
                          description='SI units for density',
                          validator=OneOf(_valid_sediment_units))

    # wave height and fetch have distance units
    wave_height = SchemaNode(String(),
                             description='SI units for distance',
                             validator=OneOf(_valid_dist_units))

    fetch = SchemaNode(String(),
                       description='SI units for distance',
                       validator=OneOf(_valid_dist_units))

    kinematic_viscosity = SchemaNode(String(),
                                     description='SI units for viscosity',
                                     validator=OneOf(_valid_kvis_units))

    density = SchemaNode(String(),
                         description='SI units for density',
                         validator=OneOf(_valid_density_units))


class WaterSchema(base_schema.ObjType):
    'Colander Schema for Conditions object'
    units = UnitsSchema()
    temperature = SchemaNode(Float())
    salinity = SchemaNode(Float())
    sediment = SchemaNode(Float(), missing=drop)
    wave_height = SchemaNode(Float(), missing=drop)
    fetch = SchemaNode(Float(), missing=drop)


class Water(Environment, serializable.Serializable):
    '''
    Define the environmental conditions for a spill, like water_temperature,
    atmos_pressure (most likely a constant)

    Defined in a Serializable class since user will need to set/get some of
    these properties through the client
    '''
    _ref_as = 'water'
    _state = copy.deepcopy(Environment._state)
    _field_descr = {'units': ('update', 'save'),
                    'temperature:': ('update', 'save'),
                    'salinity': ('update', 'save'),
                    'sediment': ('update', 'save'),
                    'fetch': ('update', 'save'),
                    'wave_height': ('update', 'save'),
                    'density': ('update', 'save'),
                    'kinematic_viscosity': ('update', 'save')}
    _state += [serializable.Field('units', update=True, save=True),
               serializable.Field('temperature', update=True, save=True),
               serializable.Field('salinity', update=True, save=True),
               serializable.Field('sediment', update=True, save=True),
               serializable.Field('fetch', update=True, save=True),
               serializable.Field('wave_height', update=True, save=True),
               serializable.Field('density', update=True, save=True),
               serializable.Field('kinematic_viscosity', update=True,
                                  save=True)]

    _schema = WaterSchema

    _units_type = {'temperature': ('temperature', _valid_temp_units),
                   'salinity': ('salinity', _valid_salinity_units),
                   'sediment': ('concentration in water',
                                _valid_sediment_units),
                   'wave_height': ('length', _valid_dist_units),
                   'fetch': ('length', _valid_dist_units),
                   'kinematic_viscosity': ('kinematic viscosity',
                                           _valid_kvis_units),
                   'density': ('density', _valid_density_units),
                   }

    # keep track of valid SI units for properties - these are used for
    # conversion since internal code uses SI units. Don't expect to change
    # these so make it a class level attribute
    _si_units = {'temperature': 'K',
                 'salinity': 'psu',
                 'sediment': 'kg/m^3',
                 'wave_height': 'm',
                 'fetch': 'm',
                 'density': 'kg/m^3',
                 'kinematic_viscosity': 'm^2/s'}

    def __init__(self,
                 temperature=300.0,
                 salinity=35.0,
                 sediment=.005,  # kg/m^3 oceanic default
                 wave_height=None,
                 fetch=None,
                 units=None,
                 name='Water'):
        '''
        Assume units are SI for all properties. 'units' attribute assumes SI
        by default. This can be changed, but initialization takes SI.
        '''
        # define properties in SI units
        # ask if we want unit conversion implemented here?
        self.temperature = temperature
        self.salinity = salinity
        self.sediment = sediment
        self.wave_height = wave_height
        self.fetch = fetch
        self.kinematic_viscosity = 0.000001
        self.name = name

        self.units = self._si_units
        if units is not None:
            # self.units is a property, so this is non-destructive
            self.units = units

    def __repr__(self):
        info = ("{0.__class__.__module__}.{0.__class__.__name__}"
                "(temperature={0.temperature},"
                " salinity={0.salinity})").format(self)
        return info

    __str__ = __repr__

    def get(self, attr, unit=None):
        '''
        return value in desired unit. If None, then return the value in SI
        units. The user_unit are given in 'units' attribute and each attribute
        carries the value in as given in these user_units.
        '''
        val = getattr(self, attr)

        if unit is None:
            # Note: salinity only have one units since we don't
            # have any conversions for them in unit_conversion yet - revisit
            # this per requirements
            if (attr not in self._si_units or
                    self._si_units[attr] == self._units[attr]):
                return val
            else:
                unit = self._si_units[attr]

        if unit in self._units_type[attr][1]:
            return uc.convert(self._units_type[attr][0], self.units[attr],
                              unit, val)
        else:
            # log to file if we have logger
            ex = uc.InvalidUnitError((unit, self._units_type[attr][0]))
            self.logger.error(str(ex))
            raise ex

    def set(self, attr, value, unit):
        '''
        provide a corresponding set method that requires value and units
        The attributes can be directly set. This function just sets the
        desired property and also updates the units dict
        '''
        if unit not in self._units_type[attr][1]:
            raise uc.InvalidUnitError((unit, self._units_type[attr][0]))

        setattr(self, attr, value)
        self.units[attr] = unit

    @lru_cache(2)
    def _get_density(self, salinity, temp):
        '''
        use lru cache so we don't recompute if temp is not changing
        '''
        temp_c = uc.convert('Temperature', self.units['temperature'], 'C',
                            temp)
        # sea level pressure in decibar - don't expect atmos_pressure to change
        # also expect constants to have SI units
        rho = gsw.rho(salinity, temp_c, constants.atmos_pressure * 0.0001)

        return rho

    @property
    def density(self):
        '''
        return the density based on water salinity and temperature. The
        salinity is in 'psu'; it is not being converted to absolute salinity
        units - for our purposes, this is sufficient. Using gsw.rho()
        internally which expects salinity in absolute units.
        '''
        return self._get_density(self.salinity, self.temperature)

    def update_from_dict(self, data):
        '''
        override base class:

        'fetch' and 'wave_height' get dropped by colander if value is None.
        In this case, toggle the values back to None.
        '''
        for attr in ('fetch', 'wave_height'):
            if attr not in data:
                setattr(self, attr, None)

        super(Water, self).update_from_dict(data)

    @property
    def units(self):
        if not hasattr(self, '_units'):
            self._units = {}

        return self._units

    @units.setter
    def units(self, u_dict):
        if not hasattr(self, '_units'):
            self._units = {}

        for prop, unit in u_dict.iteritems():
            if prop in self._units_type:
                if unit not in self._units_type[prop][1]:
                    msg = ("{0} are invalid units for {1}.  Ignore it."
                           .format(unit, prop))
                    self.logger.error(msg)
                    # should we raise error?
                    raise uc.InvalidUnitError(msg)

            # allow user to add new keys to units dict.
            # also update prop if unit is valid
            self._units[prop] = unit

    def _convert_sediment_units(self, from_, to):
        '''
        used internally to convert to/from sediment units.
        '''
        if from_ == to:
            return self.sediment

        if from_ == 'mg/l':
            # convert to kg/m^3
            return self.sediment / 1000.0
        else:
            return self.sediment * 1000.0


def env_from_netCDF(filename=None, dataset=None,
                    grid_file=None, data_file=None, _cls_list=None,
                    **kwargs):
    '''
        Returns a list of instances of environment objects that can be produced
        from a file or dataset.  These instances will be created with a common
        underlying grid, and will interconnect when possible.
        For example, if an IceAwareWind can find an existing IceConcentration,
        it will use it instead of instantiating another. This function tries
        ALL gridded types by default. This means if a particular subclass
        of object is possible to be built, it is likely that all it's parents
        will be built and included as well.

        If you wish to limit the types of environment objects that will
        be used, pass a list of the types using "_cls_list" kwarg
    '''
    def attempt_from_netCDF(cls, **klskwargs):
        obj = None
        try:
            obj = c.from_netCDF(**klskwargs)
        except Exception as e:
            import logging
            logging.warn('''Class {0} could not be constituted from netCDF file
                                    Exception: {1}'''.format(c.__name__, e))
        return obj

    from gnome.environment.gridded_objects_base import Variable, VectorVariable
    from gridded.utilities import get_dataset
    from gnome.environment import PyGrid, Environment

    new_env = []

    if filename is not None:
        data_file = filename
        grid_file = filename

    ds = None
    dg = None
    if dataset is None:
        if grid_file == data_file:
            ds = dg = get_dataset(grid_file)
        else:
            ds = get_dataset(data_file)
            dg = get_dataset(grid_file)
    else:
        if grid_file is not None:
            dg = get_dataset(grid_file)
        else:
            dg = dataset
        ds = dataset
    dataset = ds

    grid = kwargs.pop('grid', None)
    if grid is None:
        grid = PyGrid.from_netCDF(filename=filename, dataset=dg, **kwargs)
        kwargs['grid'] = grid

    if _cls_list is None:
        scs = copy.copy(Environment._subclasses)
    else:
        scs = _cls_list

    for c in scs:
        if (issubclass(c, (Variable, VectorVariable)) and
                not any([isinstance(o, c) for o in new_env])):
            clskwargs = copy.copy(kwargs)
            obj = None

            try:
                req_refs = c._req_refs
            except AttributeError:
                req_refs = None

            if req_refs is not None:
                for ref, klass in req_refs.items():
                    for o in new_env:
                        if isinstance(o, klass):
                            clskwargs[ref] = o

                    if ref in clskwargs.keys():
                        continue
                    else:
                        obj = attempt_from_netCDF(c,
                                                  filename=filename,
                                                  dataset=dataset,
                                                  grid_file=grid_file,
                                                  data_file=data_file,
                                                  **clskwargs)
                        clskwargs[ref] = obj

                        if obj is not None:
                            new_env.append(obj)

            obj = attempt_from_netCDF(c,
                                      filename=filename,
                                      dataset=dataset,
                                      grid_file=grid_file,
                                      data_file=data_file,
                                      **clskwargs)

            if obj is not None:
                new_env.append(obj)

    return new_env


def ice_env_from_netCDF(filename=None, **kwargs):
    '''
        A short function to generate a list of all the 'ice_aware' classes
        for use in env_from_netCDF (this excludes GridCurrent, GridWind,
        GridTemperature, etc.)
    '''
    from gnome.environment import Environment
    cls_list = Environment._subclasses
    ice_cls_list = [c for c in cls_list
                    if (hasattr(c, '_ref_as') and 'ice_aware' in c._ref_as)]

    return env_from_netCDF(filename=filename, _cls_list=ice_cls_list, **kwargs)


def get_file_analysis(filename):
    env = env_from_netCDF(filename=filename)
    # classes = copy.copy(Environment._subclasses)

    if len(env) > 0:
        report = ['Can create {0} types of environment objects'
                  .format(len([env.__class__ for e in env]))]
        report.append('Types are: {0}'.format(str([e.__class__ for e in env])))

    report = report + grid_detection_report(filename)

    return report


def grid_detection_report(filename):
    from gnome.environment.gridded_objects_base import PyGrid

    topo = PyGrid._find_topology_var(filename)
    report = ['Grid report:']

    if topo is None:
        report.append('    A standard grid topology was not found in the file')
        report.append('    topology breakdown future feature')
    else:
        report.append('    A grid topology was found in the file: {0}'
                      .format(topo))

    return report
