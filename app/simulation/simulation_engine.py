'''
Copyright (C) 2015 Jeison Pacateque, Santiago Puerto, Wilmar Fernandez

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
'''

from .fem_mechanics import FEMMechanics
from .thermal_model import ThermalModel
from .chemical_model import ChemicalModel
import numpy as np
from .material import Material
import copy
import os
from scipy.misc import imsave

class SimulationEngine(object):
    """
    This class configures the sample as a materials array in order to run the
    simulations defined in the thermal, mechanical and chemical models.
    """
    def __init__(self, collection, slice_id, **physical_cons):

        self.collection = collection

        # materials creation
        self.mastic = Material('mastic',
                               physical_cons['mastic_YM'], # young modulus
                               physical_cons['mastic_TC'], # thermal conducticity
                               physical_cons['mastic_CH']) # chemical

        self.aggregate = Material('aggregate',
                                  physical_cons['aggregate_YM'],
                                  physical_cons['aggregate_TC'],
                                  physical_cons['aggregate_CH'])

        self.airvoid = Material('airvoid',
                                physical_cons['air_YM'],
                                physical_cons['air_TC'],
                                physical_cons['air_CH'])

        vertical_slice = self._loadVerticalSlice(slice_id)

        # Structure data where the simulation takes place
        self.matrix_materials = self._getMatrixMaterials(vertical_slice)
        self.printToTxt()

    def printToTxt(self):
        r"""This function saves in a txt and jpg file the values of the Young's
        modulus for each material on the vertical slice selected by the user
        when the simulation is configured."""

        print("Exporting matrix materials...")
        # matrix_modulus = np.empty([self.matrix_materials.shape[0], self.matrix_materials.shape[1]], dtype=int)
        matrix_modulus = np.empty(self.matrix_materials.shape, dtype=int)

        # Creates the folder for the output
        if not os.path.exists("plain_images"):
            os.makedirs("plain_images")

        # Iterate over the slice to obtain the modulus from each node
        for i in range(self.matrix_materials.shape[0]):
            for j in range(self.matrix_materials.shape[1]):
                matrix_modulus[i, j] = self.matrix_materials[i, j].young_modulus

        # Saves the files to the plain_images folder
        np.savetxt('plain_images/materials.txt', matrix_modulus, delimiter=',', fmt='%i')
        imsave('plain_images/materials.jpg', matrix_modulus)


    def _loadVerticalSlice(self, slice_id):
        """Cut the slice of the collection in the position id"""
        vertical_slice = self.collection[:, :, slice_id]
        vertical_slice = vertical_slice.copy() # avoid side effects
        return vertical_slice.transpose()

    def _getMatrixMaterials(self, vertical_slice):
        """Create the matrix material from a vertical slice"""
        material_matrix = np.empty(vertical_slice.shape, dtype=object)

        for (x,y), _ in np.ndenumerate(vertical_slice):
            if vertical_slice[x, y] == 2:
                material_matrix[x,y] = copy.deepcopy(self.aggregate)
            elif vertical_slice[x,y] == 1:
                material_matrix[x,y] = copy.deepcopy(self.mastic)
            elif vertical_slice[x,y] == 0 or  vertical_slice[x,y] == -1:
                material_matrix[x,y] = copy.deepcopy(self.airvoid)

        print("Materials matrix created, size:", material_matrix.shape)
        return material_matrix

    def _calcNewModules(self, MM):
        print("Recalculating Young's modules...")
        for i in range(MM.shape[0]):
            for j in range(MM.shape[1]):
                if MM[i,j].phase == 'mastic':
                    if MM[i,j].temperature <= 20:
                        MM[i,j].young_modulus = 16030

                    elif MM[i,j].temperature <= 35:
                        MM[i,j].young_modulus = 5148

                    else:
                        MM[i,j].young_modulus = 1527

    def simulationCicle(self, **inputs):
#==============================================================================
#       Thermal model implementation (Every model should run on a loop)
#==============================================================================
        max_TC = max(self.mastic.thermal_conductivity,
                     self.airvoid.thermal_conductivity,
                     self.aggregate.thermal_conductivity)

        self.chemical = ChemicalModel(self.matrix_materials)
        self.chemical.applySimulationConditions(74.47)
        self.matrix_materials = self.chemical.simulate()

        self.mechanics = FEMMechanics(self.matrix_materials)
        self.mechanics.applySimulationConditions(inputs['force_input'])
        self.matrix_materials = self.mechanics.simulate()

        data1 = self.matrix_materials.copy()

        self.thermal = ThermalModel(self.matrix_materials, max_TC)
        self.thermal.applySimulationConditions()
        self.matrix_materials = self.thermal.simulate(inputs['thermal_steps'])

        self._calcNewModules(self.matrix_materials)
        # Change the EA in order to run the second chemical model

        self.chemical = ChemicalModel(self.matrix_materials)
        #A little change in the energy activation(EA) is emplemented
        # from a increase of 3.13 of the rca in three moths
        # it's obtained the following change in EA
        # 3.9700659563673262303399289700659563673262303399289700659*10e-7 each second
        # in 4 hours, that is, 144000 seconds, rca would increase 313/5475
        self.chemical.applySimulationConditions(313/5475.)
        self.matrix_materials = self.chemical.simulate()

        self.mechanics = FEMMechanics(self.matrix_materials)
        self.mechanics.applySimulationConditions(inputs['force_input'])
        self.matrix_materials = self.mechanics.simulate()

        data2 = self.matrix_materials.copy()

        return data1, data2