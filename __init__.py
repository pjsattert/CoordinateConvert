# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CoordinateConversion
                                 A QGIS plugin
 Convert points between 2D coordinate systems
                             -------------------
        begin                : 2016-06-28
        copyright            : (C) 2016 by Peter Satterthwaite
        email                : pjsattert@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load CoordinateConversion class from file CoordinateConversion.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .coordinate_conversion import CoordinateConversion
    return CoordinateConversion(iface)
