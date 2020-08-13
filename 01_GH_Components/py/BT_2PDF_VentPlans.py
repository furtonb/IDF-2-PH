## IDF2PHPP: A Plugin for exporting an EnergyPlus IDF file to the Passive House Planning Package (PHPP). Created by blgdtyp, llc# # This component is part of IDF2PHPP.# # Copyright (c) 2020, bldgtyp, llc <info@bldgtyp.com> # IDF2PHPP is free software; you can redistribute it and/or modify # it under the terms of the GNU General Public License as published # by the Free Software Foundation; either version 3 of the License, # or (at your option) any later version. # # IDF2PHPP is distributed in the hope that it will be useful,# but WITHOUT ANY WARRANTY; without even the implied warranty of # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the # GNU General Public License for more details.# # For a copy of the GNU General Public License# see <http://www.gnu.org/licenses/>.# # @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>#"""Takes in a list of Honeybee zones and outputs print-ready (floor plan) objects for the Ventilation areas. Will pull out any 'PHPP Room' information from the zones and create surfaces, color them by fresh-air ventilation airflow type (supply, extract, transfer), and create room-tags based on the data. Be sure you've used the 'Create PHPP Rooms' to assign parameters to the zones and geometry correctly before trying to use this.-EM June. 22, 2020    Args:        _HBZones: A list of the Honeybee zone objects which are being analyzed in the model.        units_: <Optional> Enter either 'IP' or 'SI'. Default if nothing is input is 'SI'.        colors_: <not used yet>    Returns:        filenames_: A list of autogenerated Filenames for use if you want.        geom_: A Tree of the surfaces as Meshes, colored by Ventilation Type. Each branch of the tree will become a separate page in the final PDF. Connect to the '_geomToBake' input on the '2PDF | Print' component        annotationTxt_: A Tree of Room Data tags for printing. Connect to the '_notesToBake' input on the '2PDF | Print' component        annotationCP_: A Tree of Room center points (X,Y,Z). Useful for locating Room Tag information. Connect to the '_noteLocations' input on the '2PDF | Print' component        tableHeaders_: A list of the Headers for the Data Table        tableData_: A Tree of all the data for the Data Table. Each Branch corresponds to one row in the table (one room)"""ghenv.Component.Name = "BT_2PDF_VentPlans"ghenv.Component.NickName = "2PDF | Vent Plans"ghenv.Component.Message = 'JUN_22_2020'ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.applicationghenv.Component.Category = "BT"ghenv.Component.SubCategory = "03 | PDF"import rhinoscriptsyntax as rsimport scriptcontext as scimport Grasshopper.Kernel as ghKfrom System import Objectfrom Grasshopper import DataTreefrom Grasshopper.Kernel.Data import GH_Pathimport ghpythonlib.components as ghcdef roomCenterPt(_srfcs):    srfcCenters = []    for eachSrfc in _srfcs:        srfcCenters.append(ghc.Area(eachSrfc).centroid)    roomCenter = ghc.Average(srfcCenters)        return roomCenterdef colorMeshFromRoom(_room):    """Returns a mesh, colored by some logic        Takes in a room, converts it to     a mesh and colors it depending on the type of     fresh-air venilation flow (Sup, Ext, Mixed)    """        room_srfcs_colored = []    for srfcCount, srfc in enumerate(_room.TFAsurface):        if _room.V_sup > 0 and _room.V_eta == 0:            color = ghc.ColourRGB(255,183,227,238) # Blueish        elif _room.V_sup == 0 and _room.V_eta > 0:            color = ghc.ColourRGB(255,246,170,154) # Redish        elif _room.V_sup > 0 and _room.V_eta > 0:            color = ghc.ColourRGB(255,234,192,240) # White        else:            color = ghc.ColourRGB(255,235,235,235) # White                room_srfcs_colored.append( ghc.MeshColours(srfc, color) )        return room_srfcs_coloredhb_hive = sc.sticky["honeybee_Hive"]()HBZoneObjects = hb_hive.callFromHoneybeeHive(_HBZones)filenames_ = []geom_ = DataTree[Object]()annotationCP_ = DataTree[Object]()annotationTxt_ = DataTree[Object]()tableHeaders_ = DataTree[Object]()tableData_ = DataTree[Object]()try:    if units_.upper() == 'IP' or units_.upper() == 'CFM':        unitFactor_flow = 0.588577779 #m3/h ---> cfm        unitFactor_area = 10.76391042 #m2---> ft2        unitFactor_vol = 35.31466672 #m3---> ft3        unit_Flow = 'cfm'        unit_Area = 'ft2'        unit_Vol = 'ft3'except:    unitFactor_flow = 1.0    unitFactor_area = 1.0    unitFactor_vol = 1.0    unit_Flow = 'm3/h'    unit_Area = 'm2'    unit_Vol = 'm3'if HBZoneObjects:    # Sort the zones by name. Grr.....    HBZoneObjects_sorted = sorted(HBZoneObjects, key=lambda zone: zone.name)        for zoneBranchNum, zone in enumerate(HBZoneObjects_sorted):        filenames_.append('VENTILATION PLAN {}'.format(zoneBranchNum+1))                for roomBranchNum, room in enumerate(zone.PHPProoms):            # For each room, look at each surface in the room, convert it to            # a mesh, and re-color it based on the type of ventilation airflow            # (supply, extract, transfer). When done, add the new mesh to            # and output tree 'geom_' for passing                        geom_.AddRange(colorMeshFromRoom(room), GH_Path(zoneBranchNum))                                    # For each room, pull out the relevant data for a tag that will go            # right ontop of surface in the final PDF. Also get the            # Center Point for each annotation tag                        annotationTxt = "{}-{}\nVsup: {:.0f} {}\nVeta: {:.0f} {}".format(room.RoomNumber, room.RoomName, room.V_sup*unitFactor_flow, unit_Flow, room.V_eta*unitFactor_flow, unit_Flow)            annotationTxt_.Add(annotationTxt, GH_Path(zoneBranchNum))            annotationCP_.Add(roomCenterPt(room.TFAsurface), GH_Path(zoneBranchNum))                        # Get the Room's parameters and add to the Table            roomData = [[room.HostZoneName, 'Zone'],                        [room.RoomNumber, 'Zone'],                        [room.RoomName, 'NAME'],                        [room.FloorArea_TFA*unitFactor_area,'TFA ({})'.format(unit_Area)],                        [room.RoomVentedVolume*unitFactor_vol,'Vv ({})'.format(unit_Vol)],                        [room.V_sup*unitFactor_flow, 'Sup {}'.format(unit_Flow)],                        [room.V_eta*unitFactor_flow, 'Eta {}'.format(unit_Flow)],                        [room.V_trans*unitFactor_flow, 'Tran {}'.format(unit_Flow)],                        [room.VentSystemName, 'Unit']                        ]            if tableHeaders_.BranchCount == 0:                tableHeaders_.AddRange([v[1] for i, v in enumerate(roomData)], GH_Path(0))            tableData_.AddRange([v[0] for i, v in enumerate(roomData)], GH_Path(tableData_.BranchCount+1))