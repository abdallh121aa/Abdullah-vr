# -*- coding: utf-8 -*-
# file: blendervr/loader/__init__.py

## Copyright (C) LIMSI-CNRS (2014)
##
## contributor(s) : Jorge Gascon, Damien Touraine, David Poirier-Quinot,
## Laurent Pointal, Julian Adenauer,
##
## This software is a computer program whose purpose is to distribute
## blender to render on Virtual Reality device systems.
##
## This software is governed by the CeCILL  license under French law and
## abiding by the rules of distribution of free software.  You can  use,
## modify and/ or redistribute the software under the terms of the CeCILL
## license as circulated by CEA, CNRS and INRIA at the following URL
## "http://www.cecill.info".
##
## As a counterpart to the access to the source code and  rights to copy,
## modify and redistribute granted by the license, users are provided only
## with a limited warranty  and the software's author,  the holder of the
## economic rights,  and the successive licensors  have only  limited
## liability.
##
## In this respect, the user's attention is drawn to the risks associated
## with loading,  using,  modifying and/or developing or reproducing the
## software by the user in light of its specific status of free software,
## that may mean  that it is complicated to manipulate,  and  that  also
## therefore means  that it is reserved for developers  and  experienced
## professionals having in-depth computer knowledge. Users are therefore
## encouraged to load and test the software's suitability as regards their
## requirements in conditions enabling the security of their systems and/or
## data to be ensured and,  more generally, to use and operate it in the
## same conditions as regards security.
##
## The fact that you are presently reading this means that you have had
## knowledge of the CeCILL license and that you accept its terms.
##

import sys
import os
from .. import *
from ..tools import logger

ELEMENTS_MAIN_PREFIX = 'BlenderVR:'


def main():
    if not is_creating_loader() and not is_console():
        sys.exit()


class Creator:
    def __init__(self, logger):

        self._logger = logger
        self._logger.setLevel('debug')

        self._input_blender_file = sys.argv[(sys.argv.index('--') + 1)]
        self._output_blender_file = self._input_blender_file.split('.')
        self._output_blender_file.insert(-1, 'vr')
        self._output_blender_file = '.'.join(self._output_blender_file)
        self._output_blender_file = os.path.join(
                    os.path.dirname(self._output_blender_file),
                    '.' + os.path.basename(self._output_blender_file))

        self._output_blender_file = self._output_blender_file.replace('\\', '/')

    def process(self):
        if is_creating_loader():
            import bpy
            bpy.ops.wm.open_mainfile(filepath=self._input_blender_file)

            scene = bpy.context.scene

            # Update frame_type of the scene, otherwise, there will be black borders ...
            scene.game_settings.frame_type = 'SCALE'

            # if the file has multiple cameras take only the active one
            camera = scene.camera

            if camera:
                scene.objects.active = camera

                SENSOR = ELEMENTS_MAIN_PREFIX + 'Sensor'
                bpy.ops.logic.sensor_add(type='ALWAYS', name=SENSOR)
                sensor = camera.game.sensors.get(SENSOR)
                sensor.use_pulse_true_level = True

                CONTROLLER = ELEMENTS_MAIN_PREFIX + 'Controller'
                bpy.ops.logic.controller_add(type='PYTHON', name=CONTROLLER)
                controller = camera.game.controllers.get(CONTROLLER)
                controller.mode = 'MODULE'
                controller.module = 'blendervr.run'
                controller.use_priority = True

                ACTUATOR = ELEMENTS_MAIN_PREFIX + 'OculusDK2:Filter'
                bpy.ops.logic.actuator_add(type='FILTER_2D', name=ACTUATOR)
                actuator = camera.game.actuators.get(ACTUATOR)
                actuator.mode = 'CUSTOMFILTER'

                TEXT = ELEMENTS_MAIN_PREFIX + 'Oculus:GLSL'
                shader = bpy.data.texts.new(TEXT)
                actuator.glsl_shader = shader
                shader.from_string(self._getScreenShader())

                bpy.ops.object.game_property_new(type='FLOAT', name="screen_width")
                bpy.ops.object.game_property_new(type='FLOAT', name="screen_height")

                controller.link(sensor=sensor)
                controller.link(actuator=actuator)

                processor_files = sys.argv[(sys.argv.index('--') + 2):]

                from blendervr.processor import _getProcessor
                processor_class = _getProcessor(processor_files,
                                                self._logger, True)
                processor = processor_class(self)

                processor.process(controller)

                bpy.ops.wm.save_as_mainfile(copy=True,
                                    filepath=self._output_blender_file,
                                    relative_remap=True)

        elif is_console():
            print(self._output_blender_file)

    def _getScreenShader(self):
        import os
        folderpath = os.path.dirname(os.path.abspath(__file__))
        filepath = "/".join((folderpath, 'oculus_dk2.glsl'))
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        return data


import os
if os.environ.get('READTHEDOCS', False) != 'True':
    main()
