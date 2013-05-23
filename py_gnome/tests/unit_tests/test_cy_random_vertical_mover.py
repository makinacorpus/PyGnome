"""
unit tests cython wrapper

designed to be run with py.test
"""

import numpy as np

from gnome import basic_types
from gnome.cy_gnome import cy_random_vertical_mover,cy_helpers
import cy_fixtures

import pytest


def test_exceptions():
    """
    Test ValueError exception thrown if improper input arguments
    """
    with pytest.raises(ValueError):
        cy_random_vertical_mover.CyRandomVerticalMover(vertical_diffusion_coef=0)

    
class TestRandomVertical():
    cm = cy_fixtures.CyTestMove()
    rm = cy_random_vertical_mover.CyRandomVerticalMover(vertical_diffusion_coef=5)    
    def move(self, delta): 
        self.rm.prepare_for_model_run()
        
        self.rm.prepare_for_model_step(self.cm.model_time, self.cm.time_step)
        self.rm.get_move( self.cm.model_time,
                          self.cm.time_step, 
                          self.cm.ref,
                          delta,
                          self.cm.status,
                          basic_types.spill_type.forecast,
                          0)
        
    def test_move(self):
        """
        test that it moved
        """
        self.move(self.cm.delta)
        np.set_printoptions(precision=4)
        print 
        print  "vertical_diffusion_coef = {0:0.1f}".format(self.rm.vertical_diffusion_coef) + " get_move output:"
        print  self.cm.delta.view(dtype=np.float64).reshape(-1,3)
        assert np.all(self.cm.delta['z'] != 0)
        #assert np.all(self.cm.delta['lat'] != 0)
        #assert np.all(self.cm.delta['long'] != 0)
        
    def test_zero_coef(self):
        """
        ensure no move for 0 vertical diffusion coefficient 
        """
        self.rm.vertical_diffusion_coef = 0
        new_delta = np.zeros((self.cm.num_le,), dtype=basic_types.world_point)
        self.move(new_delta)
        self.rm.vertical_diffusion_coef = 5        
        assert np.all(new_delta.view(dtype=np.double).reshape(1,-1) == 0)
        
    def test_update_coef(self):
        """
        Test that the move is different from original move since vertical diffusion coefficient is different
        use the py.test -s flag to view the difference between the two
        """
        #cy_helpers.srand(1)    # this now happens in conftest.py before every test
        np.set_printoptions(precision=6)
        delta = np.zeros((self.cm.num_le,), dtype=basic_types.world_point)
        self.move(delta)    # get the move before changing the coefficient
        print 
        print  "vertical_diffusion_coef = {0.vertical_diffusion_coef}".format(self.rm) + " get_move output:"
        print delta.view(dtype=np.float64).reshape(-1,3)
        self.rm.vertical_diffusion_coef = 10
        assert self.rm.vertical_diffusion_coef == 10
        
        cy_helpers.srand(1)
        new_delta = np.zeros((self.cm.num_le,), dtype=basic_types.world_point)
        self.move(new_delta)    # get the move after changing coefficient
        print
        print  "vertical_diffusion_coef = {0.vertical_diffusion_coef}".format(self.rm)+ " get_move output:"
        print new_delta.view(dtype=np.float64).reshape(-1,3)
        print
        print "-- Norm of difference between movement vector --"        
        print self._diff(delta, new_delta).reshape(-1,1)
        assert np.all(delta['z'] != new_delta['z'])
        #assert np.all(delta['lat'] != new_delta['lat'])
        #assert np.all(delta['long'] != new_delta['long'])
        
        self.rm.vertical_diffusion_coef = 5        # reset it
    
    def test_seed(self):
        """
        Since seed is not reset, the move should be repeatable
        """
        #cy_helpers.srand(1)    # this now happens in conftest.py before every test
        delta = np.zeros((self.cm.num_le,), dtype=basic_types.world_point)
        self.move(delta)
        cy_helpers.srand(1)
        new_delta = np.zeros((self.cm.num_le,), dtype=basic_types.world_point)
        self.move(new_delta)
        print
        print "-- Do not reset seed and call get move again to get identical results --"
        print "get_move results 1st time:"
        print delta.view(dtype=np.float64).reshape(-1,3)
        print "get_move results 2nd time - same seed:"
        print new_delta.view(dtype=np.float64).reshape(-1,3)
        print
        print "-- Norm of difference between movement vector --"
        print self._diff(delta, new_delta)
        assert np.all(delta['lat'] == new_delta['lat'])
        assert np.all(delta['long'] == new_delta['long'])    
    
    def _diff(self, delta, new_delta):
        """
        gives the norm of the (delta-new_delta)
        """
        diff = delta.view(dtype=basic_types.world_point_type).reshape(-1,3)-new_delta.view(dtype=basic_types.world_point_type).reshape(-1,3)
        return np.sum(diff**2, axis=1)**.5
    
if __name__ == "__main__":
    """
    This makes it easy to use this file to debug the lib_gnome DLL 
    through Visual Studio
    """
    tr = TestRandom()
    #tr.test_move()
    #tr.test_update_coef()
    tr.test_seed()
