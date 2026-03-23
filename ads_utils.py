import os
import shutil

from keysight.ads import de
from keysight.ads.de import PointF
from keysight.ads.de import db_uu as db
from keysight.ads.de.db import Transaction

import pathlib
import keysight.ads.dds as dds

from bvd_com_computations import BVD
from bvd_com_computations import COM

from decimal import Decimal

FORCE_RECREATE = True

CELL_BVD_LOSSY = "BVD_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_FILTER_BVD = "Ladder_Filter_BVD"   # celda jerárquica (schematic)
CELL_COM_LOSSY = "COM_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_FILTER_COM = "Ladder_Filter_COM"   # celda jerárquica (schematic)

def test_import_keysight_ads_de_example() -> None:
    try:
        from keysight.ads import de
    except ImportError as e:
        raise ImportError(
            "Failed to import keysight.ads.de. Verify your environment has been configured properly."
        ) from e

    version = de.version()

    assert version >= 630, "Version of keysight.ads.de is not as expected."
    print(f"Import of keysight.ads.de successful in ADS version {de.version()}.")

def create_and_open_an_empty_workspace(workspace_path: str):
    # Ensure there isn't already a workspace open
    if de.workspace_is_open():
        de.close_workspace()

    # Cannot create a workspace if the directory already exists
    if os.path.exists(workspace_path):
        if FORCE_RECREATE:
            shutil.rmtree(workspace_path)
        else:
            return None

    # Create the workspace
    workspace = de.create_workspace(workspace_path)
    # Open the workspace
    workspace.open()
    # Return the open workspace and close when it finished
    return workspace

def create_a_library_and_add_it_to_the_workspace(workspace: de.Workspace, library_name: str) -> None:
    # assert workspace.path is not None
    # Libraries can only be added to an open workspace
    assert workspace.is_open
    # We'll create a library in the directory of the workspace
    library_path = workspace.path / library_name
    # Create the library
    de.create_new_library(library_name, library_path)
    # And add it to the workspace (update lib.defs)
    workspace.add_library(library_name, library_path, de.LibraryMode.SHARED)
    library = workspace.open_library(library_name,library_path,de.LibraryMode.SHARED)
    return library

def create_SchematicAndSymbol_lossyBVD(library: de.Library, library_name: str) -> None:    
    # ========= 1) Schematic interno lossyBVD =========
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_BVD_LOSSY}:schematic")
    design = db.open_design(f"{library_name}:{CELL_BVD_LOSSY}:schematic")

    with Transaction(design) as transaction:
        # Terms
        net = design.add_net("P1")
        term = design.add_term(net, "P1", db.TermType.INPUT)
        shape = design.add_dot(db.LayerId(229), loc=PointF(0.0, 0.0))
        pin1 = design.add_pin(term, shape, angle=180.0)
        pin1.update_pin_annotation(preserve_origin=False)

        net = design.add_net("P2")
        term = design.add_term(net, "P2", db.TermType.OUTPUT)
        shape = design.add_dot(db.LayerId(229), loc=PointF(8.5, 0.0))
        pin2 = design.add_pin(term, shape)
        pin2.update_pin_annotation(preserve_origin=False)

        # Shapes
        shape = design.add_wire([PointF(x=7.0, y=1.0), PointF(x=7.0, y=0.0)])
        shape = design.add_wire([PointF(x=6.0, y=1.0), PointF(x=6.0, y=0.0)])
        shape = design.add_wire([PointF(x=1.0, y=2.5), PointF(x=1.0, y=1.5)])
        shape = design.add_wire([PointF(x=1.0, y=-0.5), PointF(x=1.0, y=0.0)])
        shape = design.add_wire([PointF(x=1.0, y=0.0), PointF(x=1.0, y=0.5)])
        shape = design.add_wire([PointF(x=4.0, y=0.0), PointF(x=4.0, y=-0.5)])
        shape = design.add_wire([PointF(x=1.0, y=-1.5), PointF(x=1.0, y=-0.5)])
        points = [PointF(x=4.0, y=-0.5), PointF(x=4.0, y=-1.5), PointF(x=2.0, y=-1.5)]
        shape = design.add_wire(points)
        shape = design.add_wire([PointF(x=5.0, y=0.0), PointF(x=6.0, y=0.0)])
        shape = design.add_wire([PointF(x=1.0, y=0.5), PointF(x=1.0, y=1.5)])
        shape = design.add_wire([PointF(x=7.5, y=0.0), PointF(x=7.0, y=0.0)])
        shape = design.add_wire([PointF(x=4.0, y=0.5), PointF(x=4.0, y=0.0)])
        shape = design.add_wire([PointF(x=2.0, y=2.5), PointF(x=2.0, y=1.5)])
        points = [PointF(x=4.0, y=0.5), PointF(x=4.0, y=1.5), PointF(x=2.0, y=1.5)]
        shape = design.add_wire(points)
        shape = design.add_wire([PointF(x=3.0, y=0.5), PointF(x=4.0, y=0.5)])

        # Instances
        inst = design.add_var_instance(name="VAR1", origin=(4.75, 3.0))
        inst.vars.update({'fs': '1/(2*pi*sqrt(La*Ca))', 'Ra': '2*pi*fs*La/Qa'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_instance("ads_rflib:C", name="Ca", origin=(2.0, -0.5))
        inst.parameters["C"].value = "Ca F"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:C", name="Cadd_ser", origin=(6.0, 0.0))
        inst.parameters["C"].value = "Cadd_ser F"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:C", name="Cadd_shu", origin=(1.0, 1.5))
        inst.parameters["C"].value = "Cadd_shu F"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:C", name="Cp", origin=(2.0, 0.5))
        inst.parameters["C"].value = "Cp F"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:L", name="La", origin=(1.0, -0.5))
        inst.parameters["L"].value = "La H"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:L", name="Ladd_gnd", origin=(7.5, 0.0))
        inst.parameters["L"].value = "Ladd_ground H"
        inst.parameters["R"].value = "2*pi*fs*Ladd_ground/Ql Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:L", name="Ladd_ser", origin=(4.0, 0.0))
        inst.parameters["L"].value = "Ladd_ser H"
        inst.parameters["R"].value = "2*pi*fs*Ladd_ser/Ql Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:L", name="Ladd_shu", origin=(1.0, -1.5))
        inst.parameters["L"].value = "Ladd_shu H"
        inst.parameters["R"].value = "2*pi*fs*Ladd_shu/Ql Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R1", origin=(1.0, 2.5))
        inst.parameters["R"].value = "Qc/(2*pi*fs*Cadd_shu) Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R2", origin=(6.0, 1.0))
        inst.parameters["R"].value = "Qc/(2*pi*fs*Cadd_ser) Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="Ra", origin=(3.0, -0.5))
        inst.parameters["R"].value = "Ra Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="Rp", origin=(1.0, 0.5))
        inst.parameters["R"].value = "Rp Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="Rs", origin=(0.0, 0.0))
        inst.parameters["R"].value = "Rs Ohm"
        inst.update_item_annotation()

        transaction.commit()

    design.save_design()
    design = None

    # ========= 2) mdlParams + ModelDef (caixeta jerárquica) =========
    formset = de.db_uu.model_lib.formsets["StdFormSet"]

    # MAIN BVD parameters
    varCp = de.db_uu.ModelParam("Cp", "Capacitance", formset, de.db_uu.ModelUnitType.CAPACITANCE)
    varCp.default_value = de.db_uu.ParamItemString("Cp", "StdForm", str("1"))
    varCp.is_displayed_by_default = True

    varCa = de.db_uu.ModelParam("Ca", "Capacitance", formset, de.db_uu.ModelUnitType.CAPACITANCE)
    varCa.default_value = de.db_uu.ParamItemString("Ca", "StdForm", str("1"))
    varCa.is_displayed_by_default = True

    varLa = de.db_uu.ModelParam("La", "Inductance", formset, de.db_uu.ModelUnitType.INDUCTANCE)
    varLa.default_value = de.db_uu.ParamItemString("La", "StdForm", str("1"))
    varLa.is_displayed_by_default = True

    # ADDITIONAL BVD parameters
    varLadd_ser = de.db_uu.ModelParam("Ladd_ser", "Inductance", formset, de.db_uu.ModelUnitType.INDUCTANCE)
    varLadd_ser.default_value = de.db_uu.ParamItemString("Ladd_ser", "StdForm", str("1"))
    varLadd_ser.is_displayed_by_default = True

    varLadd_shu = de.db_uu.ModelParam("Ladd_shu", "Inductance", formset, de.db_uu.ModelUnitType.INDUCTANCE)
    varLadd_shu.default_value = de.db_uu.ParamItemString("Ladd_shu", "StdForm", str("1"))
    varLadd_shu.is_displayed_by_default = True

    varCadd_ser = de.db_uu.ModelParam("Cadd_ser", "Capacitance", formset, de.db_uu.ModelUnitType.CAPACITANCE)
    varCadd_ser.default_value = de.db_uu.ParamItemString("Cadd_ser", "StdForm", str("1"))
    varCadd_ser.is_displayed_by_default = True

    varCadd_shu = de.db_uu.ModelParam("Cadd_shu", "Capacitance", formset, de.db_uu.ModelUnitType.CAPACITANCE)
    varCadd_shu.default_value = de.db_uu.ParamItemString("Cadd_shu", "StdForm", str("1"))
    varCadd_shu.is_displayed_by_default = True

    varLadd_ground = de.db_uu.ModelParam("Ladd_ground", "Inductance", formset, de.db_uu.ModelUnitType.INDUCTANCE)
    varLadd_ground.default_value = de.db_uu.ParamItemString("Ladd_ground", "StdForm", str("1"))
    varLadd_ground.is_displayed_by_default = True

    # OTHER BVD parameters
    varRs = de.db_uu.ModelParam("Rs", "Resistance", formset, de.db_uu.ModelUnitType.RESISTANCE)
    varRs.default_value = de.db_uu.ParamItemString("Rs", "StdForm", str("0.1"))
    varRs.is_displayed_by_default = True

    varRp = de.db_uu.ModelParam("Rp", "Resistance", formset, de.db_uu.ModelUnitType.RESISTANCE)
    varRp.default_value = de.db_uu.ParamItemString("Rp", "StdForm", str("0.01"))
    varRp.is_displayed_by_default = True

    varQl = de.db_uu.ModelParam("Ql", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varQl.default_value = de.db_uu.ParamItemString("Ql", "StdForm", str("50"))
    varQl.is_displayed_by_default = True

    varQc = de.db_uu.ModelParam("Qc", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varQc.default_value = de.db_uu.ParamItemString("Qc", "StdForm", str("50"))
    varQc.is_displayed_by_default = True

    varQa = de.db_uu.ModelParam("Qa", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varQa.default_value = de.db_uu.ParamItemString("Qa", "StdForm", str("50"))
    varQa.is_displayed_by_default = True

    model_def = de.db_uu.ModelDef(CELL_BVD_LOSSY, CELL_BVD_LOSSY)
    model_def.inst_name_prefix = "lossyBVD"
    model_def.is_sub_design = True
    model_def.parameters = [varCp, varCa, varLa, varLadd_ser, varLadd_shu, varCadd_ser, varCadd_shu, varLadd_ground, varRs, varRp, varQl, varQc, varQa]

    de.add_model_definition(library, model_def)

    # ========= 3) Symbol view (mínimo) para instanciar la caixeta =========
    assert de.version() >= 630

    design = db.create_symbol(f"{library_name}:{CELL_BVD_LOSSY}:symbol")
    design = db.open_design(f"{library_name}:{CELL_BVD_LOSSY}:symbol")

    with Transaction(design) as transaction:
        # Properties
        db.StringProp.create(design, "SymbolGenSettings", "1")

        # Terms
        net = design.add_net("P1")
        term = design.add_term(net, "P1")
        shape = design.add_dot(db.LayerId(229), loc=PointF(0.0, 0.0))
        pin1 = design.add_pin(term, shape, angle=180.0, add_annot=False)
        pin1.update_pin_annotation(preserve_origin=False)

        net = design.add_net("P2")
        term = design.add_term(net, "P2")
        shape = design.add_dot(db.LayerId(229), loc=PointF(1.0, 0.0))
        pin2 = design.add_pin(term, shape, add_annot=False)
        pin2.update_pin_annotation(preserve_origin=False)

        # Shapes
        shape = design.add_rectangle(db.LayerId(231), PointF(0.375, -0.25), PointF(0.625, 0.25))
        shape.legacy_border_thickness = db.LineThickness.THICK

        shape = design.add_line(db.LayerId(231), [PointF(x=0.75, y=0.25), PointF(x=0.75, y=-0.25)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.THICK

        shape = design.add_line(db.LayerId(231), [PointF(x=0.25, y=0.0), PointF(x=0.0, y=0.0)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.MEDIUM

        shape = design.add_line(db.LayerId(231), [PointF(x=0.25, y=0.25), PointF(x=0.25, y=-0.25)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.THICK

        shape = design.add_line(db.LayerId(231), [PointF(x=0.75, y=0.0), PointF(x=1.0, y=0.0)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.MEDIUM

        shape = design.add_text(db.LayerId(237, 244), "P1", PointF(0.275, 0.0), "Roboto", 0.06875, is_drafting=False)

        shape = design.add_text(db.LayerId(237, 244), "P2", PointF(0.725, 0.0), "Roboto", 0.06875, align="CenterRight", is_drafting=False)

        transaction.commit()

    design.save_design()
    design = None

def create_Schematic_ladderFilter_BVDlossy(library: de.Library, library_name: str, parameters: dict, list_BVD: list[BVD]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_FILTER_BVD}:schematic")
    design = db.open_design(f"{library_name}:{CELL_FILTER_BVD}:schematic")

    # READ Basic Ladder parameters
    order = int(parameters["norder_ini"])
    startBVD_type = parameters["typeseriesshunt_ini"]
    endBVD_type = ""
    option = int(parameters["option"])

    # Determine the type of the last BVD based on the order and the type of the first BVD
    if order % 2 == 0:
        endBVD_type = "shunt" if startBVD_type == "series" else "series"
    else:
        endBVD_type = "series" if startBVD_type == "series" else "shunt"

    # READ Matching network parameters
    matching_network = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    input_l = parameters["input_l"]
    lfini1 = parameters["lfini1"]
    lfini2 = parameters["lfini2"]
    cfini1 = parameters["cfini1"]
    cfini2 = parameters["cfini2"]
    
    # Sweep parameters
    fstart = parameters["fstart1"]
    fstop = parameters["fstop1"]
    npoints = parameters["npoints1"]
    
    # Grid positon parameters
    xpos = 0.0
    xpos_max = xpos
    max_size_symb = 3.0
    max_size_input = 3.0
    max_size_output = 4.0
    ypos = 0.0

    xpos_firststep = 1.25
    xstep = -1
    num_BVD = 0

    space_parallel = 1.0

    with Transaction(design) as transaction:
        # TermG1
        inst = design.add_instance("ads_simulation:TermG", name="TermG1", origin=(xpos, ypos), angle=-90.0)
        inst.parameters["Num"].value = "1"
        inst.update_item_annotation()

        xpos = xpos_max
        ypos = 0.0

        # INPUT MATCHING NETWORK: (need to know if first BVD is series or shunt)
        xstep += 1

        if startBVD_type == "series":
            # Add shunt inductor at the input
            d = Decimal(input_l)
            exp10 = d.adjusted()   # exponente base 10

            if exp10 > -10:
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep*2, y=ypos)])
                xpos += xpos_firststep*2

                inst = design.add_instance("ads_rflib:L", name="L_input", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["L"].value = "input_l H"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0

            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos_max + max_size_input, y=ypos)])

        else:
            # Add series inductor at the input
            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
            xpos += xpos_firststep

            inst = design.add_instance("ads_rflib:L", name="L_input", origin=(xpos, ypos))
            inst.parameters["L"].value = "input_l H"
            inst.update_item_annotation()
            xpos += 1.0

            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos_max + max_size_input, y=ypos)])

        xpos_max += max_size_input
        xpos = xpos_max
        ypos = 0.0

        # FIRST BVD: Start BVD ladder depending on if it is series or shunt
        # Remember to put a GROUND if BVD is shunt
        xstep += 1

        if startBVD_type == "series":
            # SERIES BVD start
            angle_BVD = 0.0
            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
            xpos += xpos_firststep

            design.add_wire([PointF(x=xpos+1.0, y=ypos), PointF(x=xpos_max + max_size_symb, y=ypos)])
        else:
            # SHUNT BVD start
            angle_BVD = -90.0
            xpos += max_size_symb/2

            points = [PointF(x=xpos-max_size_symb/2, y=ypos), PointF(x=xpos, y=ypos), PointF(x=xpos+max_size_symb/2, y=ypos)]
            design.add_wire(points)

            inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos-1.0), angle=-90.0, ads_annot=False)
        
        inst = design.add_instance((library_name, CELL_BVD_LOSSY, "symbol"), origin=(xpos, ypos), name="lossyBVD_"+str(num_BVD), angle=angle_BVD)
        inst.parameters["Cp"].value = str(list_BVD[num_BVD].cp)
        inst.parameters["Ca"].value = str(list_BVD[num_BVD].ca)
        inst.parameters["La"].value = str(list_BVD[num_BVD].la)
        inst.parameters["Ladd_ser"].value = str(list_BVD[num_BVD].ladd_ser if list_BVD[num_BVD].ladd_ser != 0.0 else 1e-20)
        inst.parameters["Ladd_shu"].value = str(list_BVD[num_BVD].ladd_shu if list_BVD[num_BVD].ladd_shu != 0.0 else 1e-20)
        inst.parameters["Cadd_ser"].value = str(list_BVD[num_BVD].cadd_ser if list_BVD[num_BVD].cadd_ser != 0.0 else 1e-20)
        inst.parameters["Cadd_shu"].value = str(list_BVD[num_BVD].cadd_shu if list_BVD[num_BVD].cadd_shu != 0.0 else 1e-20)
        inst.parameters["Ladd_ground"].value = str(list_BVD[num_BVD].ladd_ground if list_BVD[num_BVD].ladd_ground != 0.0 else 1e-20)
        inst.parameters["Rs"].value = str(list_BVD[num_BVD].rs)
        inst.parameters["Rp"].value = str(list_BVD[num_BVD].rp)
        inst.parameters["Ql"].value = str(list_BVD[num_BVD].ql)
        inst.parameters["Qc"].value = str(list_BVD[num_BVD].qc)
        inst.parameters["Qa"].value = str(list_BVD[num_BVD].qa)

        try:
            inst.update_item_annotation()
        except Exception:
            pass

        xpos_max += max_size_symb
        xpos = xpos_max
        ypos = 0.0
        num_BVD += 1


        # BVD LADDER: Add the rest of the ladder depending on the number of BVDs
        for num_BVD in range(1, order):
            if (num_BVD % 2 == 0 and startBVD_type == "series") or (num_BVD % 2 != 0 and startBVD_type == "shunt"):
                # SERIES BVD
                angle_BVD = 0.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
                xpos += xpos_firststep

                design.add_wire([PointF(x=xpos+1.0, y=ypos), PointF(x=xpos_max + max_size_symb, y=ypos)])
            else:
                # SHUNT BVD
                angle_BVD = -90.0
                xpos += max_size_symb/2

                points = [PointF(x=xpos-max_size_symb/2, y=ypos), PointF(x=xpos, y=ypos), PointF(x=xpos+max_size_symb/2, y=ypos)]
                design.add_wire(points)

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos-1.0), angle=-90.0, ads_annot=False)

            inst = design.add_instance((library_name, CELL_BVD_LOSSY, "symbol"), origin=(xpos, ypos), name="lossyBVD_"+str(num_BVD), angle=angle_BVD)
            inst.parameters["Cp"].value = str(list_BVD[num_BVD].cp)
            inst.parameters["Ca"].value = str(list_BVD[num_BVD].ca)
            inst.parameters["La"].value = str(list_BVD[num_BVD].la)
            inst.parameters["Ladd_ser"].value = str(list_BVD[num_BVD].ladd_ser if list_BVD[num_BVD].ladd_ser != 0.0 else 1e-20)
            inst.parameters["Ladd_shu"].value = str(list_BVD[num_BVD].ladd_shu if list_BVD[num_BVD].ladd_shu != 0.0 else 1e-20)
            inst.parameters["Cadd_ser"].value = str(list_BVD[num_BVD].cadd_ser if list_BVD[num_BVD].cadd_ser != 0.0 else 1e-20)
            inst.parameters["Cadd_shu"].value = str(list_BVD[num_BVD].cadd_shu if list_BVD[num_BVD].cadd_shu != 0.0 else 1e-20)
            inst.parameters["Ladd_ground"].value = str(list_BVD[num_BVD].ladd_ground if list_BVD[num_BVD].ladd_ground != 0.0 else 1e-20)
            inst.parameters["Rs"].value = str(list_BVD[num_BVD].rs)
            inst.parameters["Rp"].value = str(list_BVD[num_BVD].rp)
            inst.parameters["Ql"].value = str(list_BVD[num_BVD].ql)
            inst.parameters["Qc"].value = str(list_BVD[num_BVD].qc)
            inst.parameters["Qa"].value = str(list_BVD[num_BVD].qa)

            try:
                inst.update_item_annotation()
            except Exception:
                pass
                
            xpos_max += max_size_symb
            xpos = xpos_max
            ypos = 0.0
            xstep += 1


        # OUTPUT MATCHING NETWORK: (need to know if last BVD is series or shunt)
        xstep += 1

        design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep*2, y=ypos)])
        xpos += xpos_firststep*2

        if matching_network == "0.0":
            if endBVD_type == "series":
                # Bobina en shunt (lfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=float(max_size_symb*xstep), y=ypos)])

            else:
                # Bobina en serie (lfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                xpos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=float(max_size_symb*xstep), y=ypos)])
        else:
            # Add the matching network for the output
            if mntype1 == "s":
                # Bobina Serie (lfini1) seguida de Condensador Shunt (Cfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini1 H"
                inst.update_item_annotation()
                xpos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+space_parallel, y=ypos)])
                xpos += space_parallel

                inst = design.add_instance("ads_rflib:C", name="C_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["C"].value = "cfini2 F"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos + 2.0, y=ypos)])

            else:
                #  Condensador Shunt (Cfini1) seguido de Bobina Serie (lfini2)
                inst = design.add_instance("ads_rflib:C", name="C_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["C"].value = "cfini1 F"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+space_parallel, y=ypos)])
                xpos += space_parallel

                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                xpos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos + 2.0, y=ypos)])

        xpos_max += max_size_output
        xpos += 2.0
        ypos = 0.0


        # TermG2
        inst = design.add_instance("ads_simulation:TermG", name="TermG2", origin=(xpos, ypos), angle=-90.0)
        inst.parameters["Num"].value = "2"
        inst.update_item_annotation()


        # S parameters simulation
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 6.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        # inst.parameters["Step"].value = "(fstop-fstart)/npoints Hz"
        inst.parameters["Step"].value = "1e6 Hz"
        inst.update_item_annotation()


        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': fstart, 'fstop': fstop, 'npoints': npoints})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])

        inst = design.add_var_instance(name="VAR_MNs", origin=(5.0, 3.0))
        inst.vars.update({"input_l": input_l, "lfini1": lfini1, "lfini2": lfini2, "cfini1": cfini1, "cfini2": cfini2})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])


        # FINISH
        transaction.commit()

    design.save_design()
    design = None

    return

def create_SchematicAndSymbol_lossyCOM(library: de.Library, library_name: str) -> None:    
    # ========= 1) Schematic interno losstCOM =========
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_COM_LOSSY}:schematic")
    design = db.open_design(f"{library_name}:{CELL_COM_LOSSY}:schematic")

    with Transaction(design) as transaction:
        # Terms
        net = design.add_net("P1")
        term = design.add_numbered_term(net, "P1", 1)
        term.parameters["RefPlane"].value = "0 mil"
        shape = design.add_dot(db.LayerId(229), loc=PointF(11.0, -2.0))
        pin1 = design.add_pin(term, shape, angle=-90.0)
        pin1.update_pin_annotation(preserve_origin=False)

        net = design.add_net("P2")
        term = design.add_numbered_term(net, "P2", 2)
        term.parameters["RefPlane"].value = "0 mil"
        shape = design.add_dot(db.LayerId(229), loc=PointF(11.0, 0.0))
        pin2 = design.add_pin(term, shape, angle=90.0)
        pin2.update_pin_annotation(preserve_origin=False)

        # Shapes
        shape = design.add_wire([PointF(x=10.75, y=-6.0), PointF(x=10.75, y=-6.75)])
        shape = design.add_wire([PointF(x=5.0, y=5.0), PointF(x=6.0, y=5.0)])
        shape = design.add_wire([PointF(x=5.0, y=4.0), PointF(x=6.0, y=4.0)])
        shape = design.add_wire([PointF(x=11.0, y=5.0), PointF(x=11.0, y=5.75)])
        shape = design.add_wire([PointF(x=2.0, y=5.0), PointF(x=4.0, y=5.0)])
        shape = design.add_wire([PointF(x=0.0, y=5.0), PointF(x=0.0, y=6.0)])
        shape = design.add_wire([PointF(x=0.0, y=4.0), PointF(x=0.0, y=5.0)])
        shape = design.add_wire([PointF(x=1.0, y=5.0), PointF(x=0.0, y=5.0)])
        shape = design.add_wire([PointF(x=0.0, y=7.0), PointF(x=0.0, y=8.0)])
        shape = design.add_wire([PointF(x=6.0, y=4.0), PointF(x=9.0, y=4.0)])
        shape = design.add_wire([PointF(x=6.0, y=5.0), PointF(x=9.0, y=5.0)])
        shape = design.add_wire([PointF(x=9.0, y=4.0), PointF(x=11.0, y=4.0)])
        shape = design.add_wire([PointF(x=9.0, y=5.0), PointF(x=11.0, y=5.0)])
        shape = design.add_wire([PointF(x=9.0, y=-1.0), PointF(x=11.0, y=-1.0)])
        shape = design.add_wire([PointF(x=9.0, y=0.0), PointF(x=11.0, y=0.0)])
        shape = design.add_wire([PointF(x=9.0, y=0.0), PointF(x=6.0, y=0.0)])
        shape = design.add_wire([PointF(x=9.0, y=-1.0), PointF(x=6.0, y=-1.0)])
        shape = design.add_wire([PointF(x=6.0, y=-1.0), PointF(x=5.0, y=-1.0)])
        shape = design.add_wire([PointF(x=6.0, y=0.0), PointF(x=5.0, y=0.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=0.0, y=1.0)])
        shape = design.add_wire([PointF(x=0.0, y=3.0), PointF(x=0.0, y=2.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=0.0, y=-1.0)])
        shape = design.add_wire([PointF(x=4.0, y=0.0), PointF(x=2.0, y=0.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=1.0, y=0.0)])
        shape = design.add_wire([PointF(x=10.75, y=-4.0), PointF(x=10.75, y=-5.0)])
        shape = design.add_wire([PointF(x=10.75, y=-6.0), PointF(x=8.75, y=-6.0)])
        shape = design.add_wire([PointF(x=10.75, y=-5.0), PointF(x=8.75, y=-5.0)])
        shape = design.add_wire([PointF(x=8.75, y=-6.0), PointF(x=6.0, y=-6.0)])
        shape = design.add_wire([PointF(x=8.75, y=-5.0), PointF(x=6.0, y=-5.0)])
        shape = design.add_wire([PointF(x=6.0, y=-6.0), PointF(x=5.0, y=-6.0)])
        shape = design.add_wire([PointF(x=6.0, y=-5.0), PointF(x=5.0, y=-5.0)])
        shape = design.add_wire([PointF(x=4.0, y=-5.0), PointF(x=2.0, y=-5.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=1.0, y=-5.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=0.0, y=-6.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=0.0, y=-4.0)])
        shape = design.add_wire([PointF(x=0.0, y=-7.0), PointF(x=0.0, y=-8.0)])
        shape = design.add_wire([PointF(x=0.0, y=-2.0), PointF(x=0.0, y=-3.0)])

        # Instances
        inst = design.add_var_instance(name="VAR1", origin=(-5.375, 3.75))
        inst.vars.update({'L': '2*d', 'N': 'DigitsActiveIDT/2', 'NR': 'DigitsReflector/2', 'CT': 'Ap*N*L*epsR*eps0*exp(0.71866*tan(1.966*(duty-0.5)))', 'k0': 'pi/d'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="VAR2", origin=(-5.375, 2.125))
        inst.vars.update({'Z0': '(1-p)/(1+p)*Z0_prima', 'Z0R': '(1+p)/(1-p)*Z0_prima', 'phi': '2*alpha*L*N*sqrt(Z0_prima)', 'k': '2*pi*freq/vf', 'beta': 'sqrt((delta+k11)^2-k12^2)', 'delta': 'k-k0', 'p': '(beta-delta-k11)/k12', 'theta': '(beta*N*L)/2'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="VAR3", origin=(-5.375, -0.125))
        inst.vars.update({'duty': '0.55', 'k11': '-82053.9-j*alphaC', 'k12': '59340', 'eps0': '8.8541878176e-12', 'vf': '3741.8', 'Z0_prima': '1', 'epsR': '39.56'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="VAR4", origin=(-5.375, -2.25))
        inst.vars.update({'Rshunt': '400000', 'Rseries': '0.1', 'alphaC': '450'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="VAR5", origin=(-5.375, -3.5))
        inst.vars.update({'thetaR': '(beta*NR*L)/2', 'phiR': '2*alpha*L*NR*sqrt(Z0_prima)', 'CTR': 'Ap*NR*L*epsR*eps0*exp(0.71866*tan(1.966*(duty-0.5)))'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P1", origin=(11.0, 0.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CT"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P2", origin=(11.0, 5.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CTR"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P3", origin=(10.75, -5.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CTR"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P2", origin=(1.0, 0.0))
        inst.parameters["Z[1,1]"].value = "Z0R/(sinh(j*2*theta))"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P3", origin=(6.0, -1.0), angle=90.0)
        inst.parameters["Z[1,1]"].value = "j*2*theta*Z0/phi^2"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P4", origin=(0.0, -1.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*theta)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P5", origin=(0.0, 2.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*theta)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P6", origin=(0.0, 7.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*thetaR)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P7", origin=(0.0, 4.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*thetaR)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P8", origin=(1.0, 5.0))
        inst.parameters["Z[1,1]"].value = "Z0R/(sinh(j*2*thetaR))"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P9", origin=(0.0, -3.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*thetaR)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P10", origin=(0.0, -6.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R*tanh(j*thetaR)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P11", origin=(1.0, -5.0))
        inst.parameters["Z[1,1]"].value = "Z0R/(sinh(j*2*thetaR))"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P12", origin=(6.0, 4.0), angle=90.0)
        inst.parameters["Z[1,1]"].value = "j*2*thetaR*Z0/phiR^2"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P13", origin=(6.0, -6.0), angle=90.0)
        inst.parameters["Z[1,1]"].value = "j*2*thetaR*Z0/phiR^2"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:GROUND", name="G6", origin=(4.0, -1.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G8", origin=(1.0, 8.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G9", origin=(1.0, -8.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G12", origin=(4.0, 4.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G13", origin=(4.0, -6.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G14", origin=(11.0, 3.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G15", origin=(11.0, 5.75), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G16", origin=(10.75, -4.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G17", origin=(10.75, -7.75), ads_annot=False)

        inst = design.add_instance("ads_rflib:R", name="R1", origin=(9.0, 0.0), angle=-90.0)
        inst.parameters["R"].value = "Rshunt Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R2", origin=(11.0, -1.0), angle=-90.0)
        inst.parameters["R"].value = "Rseries Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R3", origin=(0.0, 8.0))
        inst.parameters["R"].value = "Z0_prima Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R5", origin=(0.0, -8.0))
        inst.parameters["R"].value = "Z0_prima Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R6", origin=(11.0, 4.0), angle=-90.0)
        inst.parameters["R"].value = "Rseries Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R7", origin=(9.0, 5.0), angle=-90.0)
        inst.parameters["R"].value = "Rshunt Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R8", origin=(10.75, -6.75), angle=-90.0)
        inst.parameters["R"].value = "Rseries Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R9", origin=(8.75, -5.0), angle=-90.0)
        inst.parameters["R"].value = "Rshunt Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF2", origin=(5.0, 0.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*theta*Z0)/(Z0_prima*phi)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF3", origin=(5.0, 5.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*thetaR*Z0)/(Z0_prima*phiR)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF4", origin=(5.0, -5.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*thetaR*Z0)/(Z0_prima*phiR)"
        inst.update_item_annotation()

        transaction.commit()

    design.save_design()
    design = None

    # ========= 2) mdlParams + ModelDef (caixeta jerárquica) =========
    formset = de.db_uu.model_lib.formsets["StdFormSet"]

    varD = de.db_uu.ModelParam("d", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varD.default_value = de.db_uu.ParamItemString("d", "StdForm", str("0.1"))
    varD.is_displayed_by_default = True

    varAp = de.db_uu.ModelParam("Ap", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varAp.default_value = de.db_uu.ParamItemString("Ap", "StdForm", str("0.01"))
    varAp.is_displayed_by_default = True

    varDigitsActiveIDT = de.db_uu.ModelParam("DigitsActiveIDT", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDigitsActiveIDT.default_value = de.db_uu.ParamItemString("DigitsActiveIDT", "StdForm", str("50"))
    varDigitsActiveIDT.is_displayed_by_default = True

    varDigitsReflector = de.db_uu.ModelParam("DigitsReflector", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDigitsReflector.default_value = de.db_uu.ParamItemString("DigitsReflector", "StdForm", str("50"))
    varDigitsReflector.is_displayed_by_default = True

    varAlpha = de.db_uu.ModelParam("alpha", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varAlpha.default_value = de.db_uu.ParamItemString("alpha", "StdForm", str("50"))
    varAlpha.is_displayed_by_default = True

    model_def = de.db_uu.ModelDef(CELL_COM_LOSSY, CELL_COM_LOSSY)
    model_def.inst_name_prefix = "lossyCOM"
    model_def.is_sub_design = True
    model_def.parameters = [varD, varAp, varDigitsActiveIDT, varDigitsReflector, varAlpha]

    de.add_model_definition(library, model_def)

    # ========= 3) Symbol view (mínimo) para instanciar la caixeta =========
    assert de.version() >= 630

    design = db.create_symbol(f"{library_name}:{CELL_COM_LOSSY}:symbol")
    design = db.open_design(f"{library_name}:{CELL_COM_LOSSY}:symbol")

    with Transaction(design) as transaction:
        # Terms
        net = design.add_net("P1")
        term = design.add_numbered_term(net, "P1", 1)
        term.parameters["RefPlane"].value = "0 mil"
        shape = design.add_dot(db.LayerId(229), loc=PointF(0.0, 0.0))
        pin1 = design.add_pin(term, shape, angle=180.0, add_annot=False)
        pin1.update_pin_annotation(preserve_origin=False)

        net = design.add_net("P2")
        term = design.add_numbered_term(net, "P2", 2)
        term.parameters["RefPlane"].value = "0 mil"
        shape = design.add_dot(db.LayerId(229), loc=PointF(1.0, 0.0))
        pin2 = design.add_pin(term, shape, add_annot=False)
        pin2.update_pin_annotation(preserve_origin=False)

        # Shapes
        shape = design.add_line(db.LayerId(231), [PointF(x=0.25, y=0.0), PointF(x=0.0, y=0.0)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.MEDIUM

        shape = design.add_rectangle(db.LayerId(231), PointF(0.275, -0.225), PointF(0.725, 0.225))

        shape = design.add_line(db.LayerId(231), [PointF(x=0.75, y=0.0), PointF(x=1.0, y=0.0)], arc_resolution=0.0)
        shape.legacy_border_thickness = db.LineThickness.MEDIUM

        shape = design.add_rectangle(db.LayerId(231), PointF(0.25, -0.25), PointF(0.75, 0.25))
        shape.legacy_border_thickness = db.LineThickness.MEDIUM

        shape = design.add_text(db.LayerId(237, 244), "P2", PointF(0.725, 0.0), "Arial For CAE", 0.06875, align="CenterRight", is_drafting=False)

        shape = design.add_text(db.LayerId(237, 244), "P1", PointF(0.275, 0.0), "Arial For CAE", 0.06875, is_drafting=False)

        transaction.commit()

    design.save_design()
    design = None

def create_Schematic_ladderFilter_COM(library: de.Library, library_name: str, parameters: dict, list_COM: list[COM]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_FILTER_COM}:schematic")
    design = db.open_design(f"{library_name}:{CELL_FILTER_COM}:schematic")

    # READ Basic Ladder parameters
    order = int(parameters["norder_ini"])
    startCOM_type = parameters["typeseriesshunt_ini"]
    endCOM_type = ""
    option = int(parameters["option"])

    # Determine the type of the last COM based on the order and the type of the first COM
    if order % 2 == 0:
        if startCOM_type == "series":
            endCOM_type = "shunt"
        else:            
            endCOM_type = "series"
    else:
        if startCOM_type == "series":
            endCOM_type = "series"
        else:            
            endCOM_type = "shunt"

    # READ Matching network parameters
    matching_network = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    mntype2 = parameters["mntype2"]
    input_l = parameters["input_l"]
    lfini1 = parameters["lfini1"]
    lfini2 = parameters["lfini2"]
    cfini1 = parameters["cfini1"]
    cfini2 = parameters["cfini2"]
    
    # Sweep parameters
    fstart = parameters["fstart1"]
    fstop = parameters["fstop1"]
    npoints = parameters["npoints1"]
    
    # Grid positon parameters
    xpos = 0.0
    xpos_max = xpos
    max_size_symb = 3.0
    max_size_input = 3.0
    max_size_output = 4.0
    ypos = 0.0

    xpos_firststep = 1.25
    xstep = -1
    num_COM = 0

    space_parallel = 1.0

    with Transaction(design) as transaction:
        # TermG1
        inst = design.add_instance("ads_simulation:TermG", name="TermG1", origin=(xpos, ypos), angle=-90.0)
        inst.parameters["Num"].value = "1"
        inst.update_item_annotation()

        xpos = xpos_max
        ypos = 0.0

        # INPUT MATCHING NETWORK: (need to know if first COM is series or shunt)
        xstep += 1

        if startCOM_type == "series":
            # Add shunt inductor at the input
            d = Decimal(input_l)
            exp10 = d.adjusted()   # exponente base 10

            if exp10 > -10:
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep*2, y=ypos)])
                xpos += xpos_firststep*2

                inst = design.add_instance("ads_rflib:L", name="L_input", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["L"].value = "input_l H"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0

            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos_max + max_size_input, y=ypos)])

        else:
            # Add series inductor at the input
            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
            xpos += xpos_firststep

            inst = design.add_instance("ads_rflib:L", name="L_input", origin=(xpos, ypos))
            inst.parameters["L"].value = "input_l H"
            inst.update_item_annotation()
            xpos += 1.0

            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos_max + max_size_input, y=ypos)])

        xpos_max += max_size_input
        xpos = xpos_max
        ypos = 0.0

        # FIRST COM: Start COM ladder depending on if it is series or shunt
        # Remember to put a GROUND if COM is shunt
        xstep += 1

        if startCOM_type == "series":
            # SERIES COM start
            angle_COM = 0.0
            design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
            xpos += xpos_firststep

            design.add_wire([PointF(x=xpos+1.0, y=ypos), PointF(x=xpos_max + max_size_symb, y=ypos)])
        else:
            # SHUNT COM start
            angle_COM = -90.0
            xpos += max_size_symb/2

            points = [PointF(x=xpos-max_size_symb/2, y=ypos), PointF(x=xpos, y=ypos), PointF(x=xpos+max_size_symb/2, y=ypos)]
            design.add_wire(points)

            inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos-1.0), angle=-90.0, ads_annot=False)
        
        inst = design.add_instance((library_name, CELL_COM_LOSSY, "symbol"), origin=(xpos, ypos), name="COM_"+str(num_COM), angle=angle_COM)
        inst.parameters["d"].value = str(list_COM[num_COM].d)
        inst.parameters["Ap"].value = str(list_COM[num_COM].Ap)
        inst.parameters["DigitsActiveIDT"].value = str(list_COM[num_COM].N*2)
        inst.parameters["DigitsReflector"].value = str(list_COM[num_COM].NR*2)
        inst.parameters["alpha"].value = str(list_COM[num_COM].alpha)

        try:
            inst.update_item_annotation()
        except Exception:
            pass

        xpos_max += max_size_symb
        xpos = xpos_max
        ypos = 0.0
        num_COM += 1


        # COM LADDER: Add the rest of the ladder depending on the number of COMs
        for num_COM in range(1, order):
            if (num_COM % 2 == 0 and startCOM_type == "series") or (num_COM % 2 != 0 and startCOM_type == "shunt"):
                # SERIES COM
                angle_COM = 0.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep, y=ypos)])
                xpos += xpos_firststep

                design.add_wire([PointF(x=xpos+1.0, y=ypos), PointF(x=xpos_max + max_size_symb, y=ypos)])
            else:
                # SHUNT COM
                angle_COM = -90.0
                xpos += max_size_symb/2

                points = [PointF(x=xpos-max_size_symb/2, y=ypos), PointF(x=xpos, y=ypos), PointF(x=xpos+max_size_symb/2, y=ypos)]
                design.add_wire(points)

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos-1.0), angle=-90.0, ads_annot=False)

            inst = design.add_instance((library_name, CELL_COM_LOSSY, "symbol"), origin=(xpos, ypos), name="COM_"+str(num_COM), angle=angle_COM)
            inst.parameters["d"].value = str(list_COM[num_COM].d)
            inst.parameters["Ap"].value = str(list_COM[num_COM].Ap)
            inst.parameters["DigitsActiveIDT"].value = str(list_COM[num_COM].N*2)
            inst.parameters["DigitsReflector"].value = str(list_COM[num_COM].NR*2)
            inst.parameters["alpha"].value = str(list_COM[num_COM].alpha)

            try:
                inst.update_item_annotation()
            except Exception:
                pass
                
            xpos_max += max_size_symb
            xpos = xpos_max
            ypos = 0.0
            xstep += 1


        # OUTPUT MATCHING NETWORK: (need to know if last COM is series or shunt)
        xstep += 1

        design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+xpos_firststep*2, y=ypos)])
        xpos += xpos_firststep*2

        if matching_network == "0.0":
            if endCOM_type == "series":
                # Bobina en shunt (lfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=float(max_size_symb*xstep), y=ypos)])

            else:
                # Bobina en serie (lfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                xpos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=float(max_size_symb*xstep), y=ypos)])
        else:
            # Add the matching network for the output
            if mntype1 == "s":
                # Bobina Serie (lfini1) seguida de Condensador Shunt (Cfini2)
                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini1 H"
                inst.update_item_annotation()
                xpos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+space_parallel, y=ypos)])
                xpos += space_parallel

                inst = design.add_instance("ads_rflib:C", name="C_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["C"].value = "cfini2 F"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos + 2.0, y=ypos)])

            else:
                #  Condensador Shunt (Cfini1) seguido de Bobina Serie (lfini2)
                inst = design.add_instance("ads_rflib:C", name="C_output", origin=(xpos, ypos), angle=-90.0)
                inst.parameters["C"].value = "cfini1 F"
                inst.update_item_annotation()
                ypos -= 1.0

                inst = design.add_instance("ads_rflib:GROUND", name="G"+str(xstep), origin=(xpos, ypos), angle=-90.0, ads_annot=False)
                ypos += 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos+space_parallel, y=ypos)])
                xpos += space_parallel

                inst = design.add_instance("ads_rflib:L", name="L_output", origin=(xpos, ypos))
                inst.parameters["L"].value = "lfini2 H"
                inst.update_item_annotation()
                xpos += 1.0

                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos + 2.0, y=ypos)])

        xpos_max += max_size_output
        xpos += 2.0
        ypos = 0.0


        # TermG2
        inst = design.add_instance("ads_simulation:TermG", name="TermG2", origin=(xpos, ypos), angle=-90.0)
        inst.parameters["Num"].value = "2"
        inst.update_item_annotation()


        # S parameters simulation
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 6.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        # inst.parameters["Step"].value = "(fstop-fstart)/npoints Hz"
        inst.parameters["Step"].value = "1e6 Hz"
        inst.update_item_annotation()


        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': fstart, 'fstop': fstop, 'npoints': npoints})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])

        inst = design.add_var_instance(name="VAR_MNs", origin=(5.0, 3.0))
        inst.vars.update({"input_l": input_l, "lfini1": lfini1, "lfini2": lfini2, "cfini1": cfini1, "cfini2": cfini2})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])


        # FINISH
        transaction.commit()

    design.save_design()
    design = None

    return

def createDataDisplay_basic_Sparameters():
    examples_path = pathlib.Path(__file__).parent.resolve()
    dds_file = dds.new_dds_file("amplifier.ds", examples_path)
    page = dds_file.pages[0]

    plot1 = page.add_plot()
    plot1.add_traces(["dB(S11)"])

    plot2 = page.add_plot()
    plot2.add_traces(["dB(S21)"])

    plot3 = page.add_plot(traces="dB(S12)")
    plot4 = page.add_plot(traces=["dB(S12)"])

    page.align_grid([plot1, plot2, plot3, plot4], 2, 2)

    dds_file.save("simple.dds")