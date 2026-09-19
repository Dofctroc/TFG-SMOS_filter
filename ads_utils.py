import os
import shutil
from pathlib import Path
from decimal import Decimal

from keysight.ads import de
from keysight.ads.de import PointF
from keysight.ads.de import db_uu as db
from keysight.ads.de.db import Transaction
from keysight.ads.de.db import LayerId
from keysight.edatoolbox import ads as eda_ads
from keysight.ads import subst
import keysight.ads.dds as dds
import keysight.ads.dataset as dataset

from models import *

# ========================== VARIABLES GLOBALES ===========================
CELL_BVD_LOSSY = "BVD_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_COM_LOSSY = "COM_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_FILTER_BVD = "Ladder_Filter_BVD"   # celda jerárquica (schematic)
CELL_FILTER_COM = "Ladder_Filter_COM"   # celda jerárquica (schematic)
CELL_FILTER = "Filters"                 # celda jerárquica (schematic)
CELL_DEBUG = "Debugging"
CELL_BUSBAR_LAYOUT = "Busbar_layout"

BVD_FILTER_STARTING_PIN = 1
COM_FILTER_STARTING_PIN = 3
BUSBAR_COM_STARTING_PIN = 5
TOUCHSTONE_STARTING_PIN = 7

# ========================== FUNCIONES ===========================

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

def create_and_open_an_empty_workspace(workspace_path: str) -> de.Workspace:
    # Ensure there isn't already a workspace open
    if de.workspace_is_open():
        de.close_workspace()

    # If the workspace exists, delete it before creating the new one
    if os.path.exists(workspace_path):
        shutil.rmtree(workspace_path)

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

# ===================================== CREATION OF SCHEMATICS FUNCTIONS =====================================

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

        inst = design.add_instance("ads_rflib:L", name="Ladd_ground", origin=(7.5, 0.0))
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

    varladd_ground = de.db_uu.ModelParam("Ladd_ground", "Inductance", formset, de.db_uu.ModelUnitType.INDUCTANCE)
    varladd_ground.default_value = de.db_uu.ParamItemString("Ladd_ground", "StdForm", str("1"))
    varladd_ground.is_displayed_by_default = True

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
    model_def.parameters = [varCp, varCa, varLa, varLadd_ser, varLadd_shu, varCadd_ser, varCadd_shu, varladd_ground, varRs, varRp, varQl, varQc, varQa]

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

def create_SchematicAndSymbol_lossyCOM(library: de.Library, library_name: str, com: COM) -> None:
    # ============================================= 1) Schematic interno losstCOM =============================================
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_COM_LOSSY}:schematic")
    design = db.open_design(f"{library_name}:{CELL_COM_LOSSY}:schematic")

    with Transaction(design) as transaction:
        # Terms
        net = design.add_net("P1")
        term = design.add_numbered_term(net, "P1", 1)
        shape = design.add_dot(db.LayerId(229), loc=PointF(11.0, -2.0))
        pin = design.add_pin(term, shape, angle=-90.0)

        net = design.add_net("P2")
        term = design.add_numbered_term(net, "P2", 2)
        shape = design.add_dot(db.LayerId(229), loc=PointF(11.0, 0.0))
        pin = design.add_pin(term, shape, angle=90.0)

        # Shapes
        shape = design.add_wire([PointF(x=11.5, y=-5.0), PointF(x=9.5, y=-5.0)])
        shape = design.add_wire([PointF(x=6.0, y=0.0), PointF(x=9.0, y=0.0)])
        shape = design.add_wire([PointF(x=6.0, y=-1.0), PointF(x=9.0, y=-1.0)])
        shape = design.add_wire([PointF(x=5.0, y=-6.0), PointF(x=6.0, y=-6.0)])
        shape = design.add_wire([PointF(x=5.0, y=5.0), PointF(x=6.0, y=5.0)])
        shape = design.add_wire([PointF(x=5.0, y=4.0), PointF(x=6.0, y=4.0)])
        shape = design.add_wire([PointF(x=5.0, y=0.0), PointF(x=6.0, y=0.0)])
        shape = design.add_wire([PointF(x=5.0, y=-1.0), PointF(x=6.0, y=-1.0)])
        shape = design.add_wire([PointF(x=9.5, y=-6.0), PointF(x=11.5, y=-6.0)])
        shape = design.add_wire([PointF(x=11.5, y=-4.0), PointF(x=11.5, y=-5.0)])
        shape = design.add_wire([PointF(x=9.5, y=5.0), PointF(x=11.5, y=5.0)])
        shape = design.add_wire([PointF(x=0.0, y=-2.0), PointF(x=0.0, y=-3.0)])
        shape = design.add_wire([PointF(x=0.0, y=-7.0), PointF(x=0.0, y=-8.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=0.0, y=-4.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=0.0, y=-6.0)])
        shape = design.add_wire([PointF(x=0.0, y=-5.0), PointF(x=1.0, y=-5.0)])
        shape = design.add_wire([PointF(x=4.0, y=-5.0), PointF(x=2.0, y=-5.0)])
        shape = design.add_wire([PointF(x=6.0, y=-5.0), PointF(x=5.0, y=-5.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=1.0, y=0.0)])
        shape = design.add_wire([PointF(x=4.0, y=0.0), PointF(x=2.0, y=0.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=0.0, y=-1.0)])
        shape = design.add_wire([PointF(x=0.0, y=3.0), PointF(x=0.0, y=2.0)])
        shape = design.add_wire([PointF(x=0.0, y=0.0), PointF(x=0.0, y=1.0)])
        shape = design.add_wire([PointF(x=9.0, y=0.0), PointF(x=11.0, y=0.0)])
        shape = design.add_wire([PointF(x=9.0, y=-1.0), PointF(x=11.0, y=-1.0)])
        shape = design.add_wire([PointF(x=9.5, y=4.0), PointF(x=11.5, y=4.0)])
        shape = design.add_wire([PointF(x=0.0, y=7.0), PointF(x=0.0, y=8.0)])
        shape = design.add_wire([PointF(x=1.0, y=5.0), PointF(x=0.0, y=5.0)])
        shape = design.add_wire([PointF(x=0.0, y=4.0), PointF(x=0.0, y=5.0)])
        shape = design.add_wire([PointF(x=0.0, y=5.0), PointF(x=0.0, y=6.0)])
        shape = design.add_wire([PointF(x=2.0, y=5.0), PointF(x=4.0, y=5.0)])
        shape = design.add_wire([PointF(x=11.5, y=5.0), PointF(x=11.5, y=5.75)])
        shape = design.add_wire([PointF(x=11.5, y=-6.0), PointF(x=11.5, y=-6.75)])
        shape = design.add_wire([PointF(x=6.0, y=5.0), PointF(x=9.5, y=5.0)])
        shape = design.add_wire([PointF(x=6.0, y=4.0), PointF(x=9.5, y=4.0)])
        shape = design.add_wire([PointF(x=9.5, y=-5.0), PointF(x=6.0, y=-5.0)])
        shape = design.add_wire([PointF(x=6.0, y=-6.0), PointF(x=9.5, y=-6.0)])

        # Instances
        inst = design.add_var_instance(name="Constants", origin=(-9.0, -0.25))
        inst.vars.update({'k11': "k11_real-j*alphaC", 'Rseries': str(com.rs), 'Rshunt': str(com.rp), 'Z0_prima': '1'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Impedance_IDT", origin=(-6.125, 3.75))
        inst.vars.update({'delta': 'k-k0', 'beta': 'sqrt((delta+k11)^2-k12^2)', 'p': '(beta-delta-k11)/k12', 
                          'Z0': '(1-p)/(1+p)*Z0_prima', 'Z0R': '(1+p)/(1-p)*Z0_prima'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Impedance_Refl", origin=(-6.125, 2.125))
        inst.vars.update({'delta_refl': 'k-k0_refl', 'beta_refl': 'sqrt((delta_refl+k11)^2-k12^2)', 'p_refl': '(beta_refl-delta_refl-k11)/k12', 
                          'Z0_refl': '(1-p_refl)/(1+p_refl)*Z0_prima', 'Z0R_refl': '(1+p_refl)/(1-p_refl)*Z0_prima'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Inputs", origin=(-9.0, 3.75))
        inst.vars.update({'L': '2*d', 'L_refl': '2*d_refl', 'k0': 'pi/d', 'k0_refl': 'pi/d_refl', 'k': '2*pi*freq/vp', 
                          'N': 'DigitsActiveIDT/2', 'NR': 'DigitsReflector/2'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Vars_IDT", origin=(-6.125, 0.5))
        inst.vars.update({'theta': '(beta*N*L)/2', 'phi': '2*alpha*L*N*sqrt(Z0_prima)', 'CT': 'Ap*N*L*eps_r*eps_0*exp(0.71866*tan(1.966*(duty-0.5)))'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Vars_Refl", origin=(-6.125, -0.625))
        inst.vars.update({'theta_refl': '(beta_refl*NR*L_refl)/2', 'phi_refl': '2*alpha*L_refl*NR*sqrt(Z0_prima)', 
                          'CT_refl': 'Ap*NR*L_refl*eps_r*eps_0*exp(0.71866*tan(1.966*(duty-0.5)))'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P1", origin=(11.0, 0.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CT"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P2", origin=(11.5, 5.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CT_refl"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Y1P_Eqn", name="Y1P3", origin=(11.5, -5.0), angle=-90.0)
        inst.parameters["Y[1,1]"].value = "j*2*pi*freq*CT_refl"
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
        inst.parameters["Z[1,1]"].value = "Z0R_refl*tanh(j*theta_refl)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P7", origin=(0.0, 4.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R_refl*tanh(j*theta_refl)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P8", origin=(1.0, 5.0))
        inst.parameters["Z[1,1]"].value = "Z0R_refl/(sinh(j*2*theta_refl))"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P9", origin=(0.0, -3.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R_refl*tanh(j*theta_refl)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P10", origin=(0.0, -6.0), angle=-90.0)
        inst.parameters["Z[1,1]"].value = "Z0R_refl*tanh(j*theta_refl)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P11", origin=(1.0, -5.0))
        inst.parameters["Z[1,1]"].value = "Z0R_refl/(sinh(j*2*theta_refl))"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P12", origin=(6.0, 4.0), angle=90.0)
        inst.parameters["Z[1,1]"].value = "j*2*theta_refl*Z0_refl/phi_refl^2"
        inst.update_item_annotation()

        inst = design.add_instance("ads_datacmps:Z1P_Eqn", name="Z1P13", origin=(6.0, -6.0), angle=90.0)
        inst.parameters["Z[1,1]"].value = "j*2*theta_refl*Z0_refl/phi_refl^2"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:GROUND", name="G6", origin=(4.0, -1.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G8", origin=(1.0, 8.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G9", origin=(1.0, -8.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G12", origin=(4.0, 4.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G13", origin=(4.0, -6.0), angle=-90.0, ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G14", origin=(11.5, 3.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G15", origin=(11.5, 5.75), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G16", origin=(11.5, -4.0), ads_annot=False)
        inst = design.add_instance("ads_rflib:GROUND", name="G17", origin=(11.5, -7.75), ads_annot=False)

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

        inst = design.add_instance("ads_rflib:R", name="R6", origin=(11.5, 4.0), angle=-90.0)
        inst.parameters["R"].value = "Rseries Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R7", origin=(9.5, 5.0), angle=-90.0)
        inst.parameters["R"].value = "Rshunt Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R8", origin=(11.5, -6.75), angle=-90.0)
        inst.parameters["R"].value = "Rseries Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:R", name="R9", origin=(9.5, -5.0), angle=-90.0)
        inst.parameters["R"].value = "Rshunt Ohm"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF2", origin=(5.0, 0.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*theta*Z0)/(Z0_prima*phi)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF3", origin=(5.0, 5.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*theta_refl*Z0_refl)/(Z0_prima*phi_refl)"
        inst.update_item_annotation()

        inst = design.add_instance("ads_rflib:TF", name="TF4", origin=(5.0, -5.0), mirror="MirrorY")
        inst.parameters["T"].value = "(2*theta_refl*Z0_refl)/(Z0_prima*phi_refl)"
        inst.update_item_annotation()

        transaction.commit()

    design.save_design()
    design = None

    # ============================================= 2) mdlParams + ModelDef (caixeta jerárquica) =============================================
    formset = de.db_uu.model_lib.formsets["StdFormSet"]

    varD = de.db_uu.ModelParam("d", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varD.default_value = de.db_uu.ParamItemString("d", "StdForm", "1")
    varD.is_displayed_by_default = True

    varDR = de.db_uu.ModelParam("d_refl", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDR.default_value = de.db_uu.ParamItemString("d_refl", "StdForm", "1")
    varDR.is_displayed_by_default = True

    varAp = de.db_uu.ModelParam("Ap", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varAp.default_value = de.db_uu.ParamItemString("Ap", "StdForm", "1")
    varAp.is_displayed_by_default = True

    varDigitsActiveIDT = de.db_uu.ModelParam("DigitsActiveIDT", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDigitsActiveIDT.default_value = de.db_uu.ParamItemString("DigitsActiveIDT", "StdForm", "1")
    varDigitsActiveIDT.is_displayed_by_default = True

    varDigitsReflector = de.db_uu.ModelParam("DigitsReflector", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDigitsReflector.default_value = de.db_uu.ParamItemString("DigitsReflector", "StdForm", "1")
    varDigitsReflector.is_displayed_by_default = True

    varAlpha = de.db_uu.ModelParam("alpha", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varAlpha.default_value = de.db_uu.ParamItemString("alpha", "StdForm", "1")
    varAlpha.is_displayed_by_default = True

    varVp = de.db_uu.ModelParam("vp", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varVp.default_value = de.db_uu.ParamItemString("vp", "StdForm", "1")
    varVp.is_displayed_by_default = True

    varK11 = de.db_uu.ModelParam("k11_real", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varK11.default_value = de.db_uu.ParamItemString("k11_real", "StdForm", "1")
    varK11.is_displayed_by_default = True

    varAlphaC = de.db_uu.ModelParam("alphaC", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varAlphaC.default_value = de.db_uu.ParamItemString("alphaC", "StdForm", "1")
    varAlphaC.is_displayed_by_default = True

    varK12 = de.db_uu.ModelParam("k12", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varK12.default_value = de.db_uu.ParamItemString("k12", "StdForm", "1")
    varK12.is_displayed_by_default = True

    varEpsR = de.db_uu.ModelParam("eps_r", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varEpsR.default_value = de.db_uu.ParamItemString("eps_r", "StdForm", "1")
    varEpsR.is_displayed_by_default = True

    varEps0 = de.db_uu.ModelParam("eps_0", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varEps0.default_value = de.db_uu.ParamItemString("eps_0", "StdForm", "1")
    varEps0.is_displayed_by_default = True

    varDuty = de.db_uu.ModelParam("duty", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDuty.default_value = de.db_uu.ParamItemString("duty", "StdForm", "1")
    varDuty.is_displayed_by_default = True

    model_def = de.db_uu.ModelDef(CELL_COM_LOSSY, CELL_COM_LOSSY)
    model_def.inst_name_prefix = "lossyCOM"
    model_def.is_sub_design = True
    model_def.parameters = [varD, varDR, varAp, varDigitsActiveIDT, varDigitsReflector, varAlpha, varVp, varK11, varAlphaC, varK12, varEpsR, varEps0, varDuty]

    de.add_model_definition(library, model_def)

    # ============================================= 3) Symbol view (mínimo) para instanciar la caixeta =============================================
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

def create_Schematic_ladder_filters(workspace_path: str, library_name: str, dataset_s2p_path: str, 
                                    parameters: dict, frequency_plan: FrequencyPlan, list_BVD: list[BVD], list_COM: list[COM]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_FILTER}:schematic")
    design = db.open_design(f"{library_name}:{CELL_FILTER}:schematic")
    
    # Sweep parameters
    fstart = frequency_plan.fstart
    fstop = frequency_plan.fstop
    npoints = frequency_plan.Nsteps

    with Transaction(design) as transaction:

        # =========================================== Sparameters Data Item for Comparison ===========================================
        if dataset_s2p_path is not None:
            inst = design.add_instance("ads_simulation:TermG", name=f"TermG{TOUCHSTONE_STARTING_PIN}", origin=(6.0, 3.0), angle=-90.0)
            inst.parameters["Num"].value = f"{TOUCHSTONE_STARTING_PIN}"
            inst.update_item_annotation()
            design.add_wire([PointF(6.0, 3.0), PointF(7.0, 3.0)])

            inst = design.add_instance("ads_datacmps:SnP", name="SnP1", origin=(7.0, 3.0))
            inst.parameters["NumPorts"].value = "2"
            inst.parameters["File"].value = dataset_s2p_path
            inst.parameters["Type"].value = '"touchstone"'
            inst.parameters["port_name_list"].value = "0 "
            with de.db.ExpressionContext(design) as expr_context, db.Transaction(design) as trans:
                expr_context.update_pcell_params(inst)
                trans.commit()
            inst.update_item_annotation()

            design.add_wire([PointF(7.75, 3.0), PointF(9.0, 3.0)])
            inst = design.add_instance("ads_simulation:TermG", name=f"TermG{TOUCHSTONE_STARTING_PIN+1}", origin=(9.0, 3.0), angle=-90.0)
            inst.parameters["Num"].value = f"{TOUCHSTONE_STARTING_PIN+1}"
            inst.update_item_annotation()


        # =========================================== S parameters simulation ===========================================
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 3.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        inst.parameters["Step"].value = "(fstop-fstart)/npoints Hz"
        inst.parameters["Sort"].value = "LINEAR START STEP "
        inst.parameters["CalcY"].value = "yes"
        inst.parameters["Freq"].value = " "
        inst.update_item_annotation()

        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': str(fstart), 'fstop': str(fstop), 'npoints': str(npoints)})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])

        # =========================================== Count all duplications ===========================================
        
        startBVD_type = parameters["typeseriesshunt_ini"]
        current_BVD_type = startBVD_type
        num_BVD = 0

        series_series_duplication_count = 0
        series_shunt_duplication_count = 0
        shunt_shunt_duplication_count = 0
        shunt_series_duplication_count = 0

        while num_BVD < len(list_BVD):
            split_mode =  list_BVD[num_BVD].split_info.mode
            split_total = list_BVD[num_BVD].split_info.total if split_mode else 1

            # Caso en que se duplica en paralelo
            if split_mode == "p":
                if current_BVD_type == "series":
                    k = 1
                    while k < split_total:
                        series_shunt_duplication_count += 1
                        num_BVD += 1
                        k += 1
                else:
                    k = 1
                    while k < split_total:
                        shunt_shunt_duplication_count += 1
                        num_BVD += 1
                        k += 1

            # Caso en que se duplica en serie
            elif split_mode == "s":
                if current_BVD_type == "series":
                    k = 1
                    while k < split_total:
                        series_series_duplication_count += 1
                        num_BVD += 1
                        k += 1
                else:
                    k = 1
                    while k < split_total:
                        shunt_series_duplication_count += 1
                        num_BVD += 1
                        k += 1

            num_BVD += 1
            
            current_BVD_type = "series" if current_BVD_type == "shunt" else "shunt"

        min_y_separation = max(max(series_shunt_duplication_count,shunt_series_duplication_count) * 4, 4)

        # =========================================== BVD ladder filter build ===========================================
        initial_xpos_BVD = 0
        initial_ypos_BVD = -min_y_separation*0
        initial_TermG_BVD = BVD_FILTER_STARTING_PIN
        build_ladder_filter_circuit_BVD(design, initial_xpos_BVD, initial_ypos_BVD, initial_TermG_BVD, parameters, list_BVD, library_name)

        # =========================================== COM ladder filter build ===========================================
        initial_xpos_COM = 0
        initial_ypos_COM = -min_y_separation*1
        initial_TermG_COM = COM_FILTER_STARTING_PIN
        build_ladder_filter_circuit_COM(design, initial_xpos_COM, initial_ypos_COM, initial_TermG_COM, parameters, list_COM, library_name)

        # =========================================== busbar+COM ladder filter build ===========================================
        initial_xpos_busbarCOM = 0
        initial_ypos_busbarCOM = -min_y_separation*2 - 1
        initial_TermG_busbarCOM = BUSBAR_COM_STARTING_PIN
        build_ladder_filter_circuit_busbar_COM(design, initial_xpos_busbarCOM, initial_ypos_busbarCOM, initial_TermG_busbarCOM, parameters, list_COM, library_name)


        # FINISH
        transaction.commit()

    design.save_design()

    # =========================================== EXTRAER EL NETLIST Y SIMULAR ===========================================
    netlist = design.generate_netlist()

    # Definimos dónde queremos que se guarde el archivo de datos (.ds)
    output_dir = os.path.join(workspace_path, "data")
    os.makedirs(output_dir, exist_ok=True)

    simulator = eda_ads.CircuitSimulator()
    
    # Esto bloqueará la ejecución de Python hasta que la simulación termine
    simulator.run_netlist(netlist, output_dir=output_dir)

    # Limpiamos
    design = None

    return

def build_ladder_filter_circuit_BVD(design: db.Design, initial_xpos: int, initial_ypos: int, initial_TermG: int, parameters: dict, list_BVD: list[BVD], library_name: str) -> None:
    # LECTURA DE PARÁMETROS BÁSICOS
    order = int(parameters["norder_ini"])
    startBVD_type = parameters["typeseriesshunt_ini"]
    
    if order % 2 == 0:
        endBVD_type = "shunt" if startBVD_type == "series" else "series"
    else:
        endBVD_type = "series" if startBVD_type == "series" else "shunt"

    # REDES DE ADAPTACIÓN
    matching_network = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    input_l = parameters["input_l"]
    lfini1 = parameters["lfini1"]
    lfini2 = parameters["lfini2"]
    cfini1 = parameters["cfini1"]
    cfini2 = parameters["cfini2"]

    x_margin = 1.5
    y_margin = 2.0

    xpos = float(initial_xpos)
    ypos = float(initial_ypos)

    num_BVD = 0
    ground_count = 1

    # =========================================== LADDER FILTER BVD ===========================================
    instantiate_term_g(design, f"TermG{initial_TermG}", initial_TermG, (xpos, ypos))

    # RED DE ADAPTACIÓN DE ENTRADA
    if startBVD_type == "series":
        d = Decimal(input_l)
        if d.adjusted() > -10:
            xpos = advance_x(design, xpos, ypos, x_margin)
            instantiate_rflib_element(design, "L", "L_input_BVD", (xpos, ypos), input_l + "H", -90.0)
            instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
            ground_count += 1
        xpos = advance_x(design, xpos, ypos, x_margin)
    else:
        xpos = advance_x(design, xpos, ypos, x_margin)
        instantiate_rflib_element(design, "L", "L_input_BVD", (xpos, ypos), input_l + "H", 0.0)
        xpos += 1.0
        xpos = advance_x(design, xpos, ypos, x_margin)

    ypos = float(initial_ypos)
    current_BVD_type = startBVD_type

    # BUCLE PRINCIPAL DE CONSTRUCCIÓN DE LA ESCALERA
    while num_BVD < len(list_BVD):
        # Datos del tipo de duplicado si tiene
        bvd_first = list_BVD[num_BVD]
        split_mode = bvd_first.split_info.mode
        split_total = bvd_first.split_info.total if split_mode else 1

        xpos = advance_x(design, xpos, ypos, x_margin)

        # Angulo del resonador según el tipo
        angle_BVD = 0.0 if current_BVD_type == "series" else -90.0

        # Instanciamos directamente el primer resonador
        instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))

        # Nos movemos al puerto de salida del resonador instanciado
        xpos += 1.0 if current_BVD_type == "series" else 0.0
        ypos -= 1.0 if current_BVD_type == "shunt" else 0.0

        # Caso en que se duplica en paralelo
        if split_mode == "p":
            # Si el resonador actual es SERIE
            if current_BVD_type == "series":
                xpos -= 1.0
                k = 1
                while k < split_total:
                    num_BVD += 1
                    advance_y(design, xpos+1.0, ypos, -y_margin)
                    ypos = advance_y(design, xpos, ypos, -y_margin)
                    instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))
                    k += 1
                ypos = float(initial_ypos)
                xpos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos))
                ground_count += 1
                ypos += 1.0
                k = 1
                while k < split_total:
                    num_BVD += 1
                    advance_x(design, xpos, ypos-1.0, x_margin+1.5)
                    xpos = advance_x(design, xpos, ypos, x_margin+1.5)
                    instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))
                    k += 1
                xpos = advance_x(design, xpos, ypos, x_margin)

        # Caso en que se duplica en serie
        elif split_mode == "s":
            # Si el resonador actual es SERIE
            if current_BVD_type == "series":
                k = 1
                while k < split_total:
                    num_BVD += 1
                    xpos = advance_x(design, xpos, ypos, x_margin)
                    instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))
                    xpos += 1.0
                    k += 1
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                k = 1
                while k < split_total:
                    num_BVD += 1
                    ypos = advance_y(design, xpos, ypos, -y_margin)
                    instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))
                    ypos -= 1.0
                    k += 1
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos))
                ground_count += 1
                ypos = float(initial_ypos)
                xpos = advance_x(design, xpos, ypos, x_margin)

        # Caso en que no se duplica        
        else:
            # Si el resonador actual es SERIE
            if current_BVD_type == "series":
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos))
                ground_count += 1
                ypos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin)

        current_BVD_type = "series" if current_BVD_type == "shunt" else "shunt"
        num_BVD += 1

    # OUTPUT MATCHING NETWORK (Renombrados con _BVD)
    xpos = advance_x(design, xpos, ypos, x_margin)

    if matching_network == "0.0":
        # INDUCTANCE TERMINATION - Add inductor
        if endBVD_type == "series":
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_BVD", (xpos, ypos), lfini2 + "H", -90.0)
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)
        else:
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_BVD", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

    else:
        # CL/LC MATCHING NETWORK - Add the matching network for the output
        if mntype1 == "s":
            if float(lfini1) > 0.0:
                instantiate_rflib_element(design, "L", "L_output1_BVD", (xpos, ypos), lfini1 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

            if float(cfini2) > 0.0:
                instantiate_rflib_element(design, "C", "C_output2_BVD", (xpos, ypos), cfini2 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

        else:
            if float(cfini1) > 0.0:
                instantiate_rflib_element(design, "C", "C_output1_BVD", (xpos, ypos), cfini1 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output2_BVD", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

    # TermG2
    instantiate_term_g(design, f"TermG{initial_TermG+1}", initial_TermG+1, (xpos, ypos))

    return

def build_ladder_filter_circuit_COM(design: db.Design, initial_xpos: int, initial_ypos: int, initial_TermG: int, parameters: dict, list_COM: list[COM], library_name: str) -> None:
    # READ Basic Ladder parameters
    order = int(parameters["norder_ini"])
    startCOM_type = parameters["typeseriesshunt_ini"]
    endCOM_type = ""

    # Determine the type of the last COM based on the order and the type of the first COM
    if order % 2 == 0:
        endCOM_type = "shunt" if startCOM_type == "series" else "series"
    else:
        endCOM_type = "series" if startCOM_type == "series" else "shunt"

    # READ Matching network parameters
    matching_network = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    input_l = parameters["input_l"]
    lfini1 = parameters["lfini1"]
    lfini2 = parameters["lfini2"]
    cfini1 = parameters["cfini1"]
    cfini2 = parameters["cfini2"]

    x_margin = 1.5
    y_margin = 2.0
    
    xpos = float(initial_xpos)
    ypos = float(initial_ypos)

    num_COM = 0
    ground_count = 1

    # =========================================== Ladder Filter of Lossy COMs ===========================================
    instantiate_term_g(design, f"TermG{initial_TermG}", initial_TermG, (xpos, ypos))

    # INPUT MATCHING NETWORK (Renombrados con _COM)
    if startCOM_type == "series":
        d = Decimal(input_l)
        if d.adjusted() > -10:
            xpos = advance_x(design, xpos, ypos, x_margin)
            instantiate_rflib_element(design, "L", "L_input_COM", (xpos, ypos), input_l + "H", -90.0)
            instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
            ground_count += 1
        xpos = advance_x(design, xpos, ypos, x_margin)
    else:
        xpos = advance_x(design, xpos, ypos, x_margin)
        instantiate_rflib_element(design, "L", "L_input_COM", (xpos, ypos), input_l + "H", 0.0)
        xpos += 1
        xpos = advance_x(design, xpos, ypos, x_margin) # Sumamos 1.0 por el tamaño del inductor

    ypos = initial_ypos
    current_COM_type = startCOM_type

    # BUCLE PRINCIPAL DE CONSTRUCCIÓN DE LA ESCALERA
    while num_COM < len(list_COM):
        # Datos del tipo de duplicado si tiene
        com_first = list_COM[num_COM]
        split_mode = com_first.split_info.mode
        split_total = com_first.split_info.total if split_mode else 1

        xpos = advance_x(design, xpos, ypos, x_margin)

        # Angulo del resonador según el tipo
        angle_COM = 0.0 if current_COM_type == "series" else -90.0
        
        instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
        
        # Nos movemos al puerto de salida del resonador instanciado
        xpos += 1.0 if current_COM_type == "series" else 0.0
        ypos -= 1.0 if current_COM_type == "shunt" else 0.0

        # Caso en que se duplica en paralelo
        if split_mode == "p":
            # Si el resonador actual es SERIE
            if current_COM_type == "series":
                xpos -= 1.0
                k = 1
                while k < split_total:
                    num_COM += 1
                    advance_y(design, xpos+1.0, ypos, -y_margin)
                    ypos = advance_y(design, xpos, ypos, -y_margin)
                    instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
                    k += 1
                ypos = float(initial_ypos)
                xpos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos))
                ground_count += 1
                ypos += 1.0
                k = 1
                while k < split_total:
                    num_COM += 1
                    advance_x(design, xpos, ypos-1.0, x_margin+1.5)
                    xpos = advance_x(design, xpos, ypos, x_margin+1.5)
                    instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
                    k += 1
                xpos = advance_x(design, xpos, ypos, x_margin)

        # Caso en que se duplica en serie
        elif split_mode == "s":
            # Si el resonador actual es SERIE
            if current_COM_type == "series":
                k = 1
                while k < split_total:
                    num_COM += 1
                    xpos = advance_x(design, xpos, ypos, x_margin)
                    instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
                    xpos += 1.0
                    k += 1
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                k = 1
                while k < split_total:
                    num_COM += 1
                    ypos = advance_y(design, xpos, ypos, -y_margin)
                    instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
                    ypos -= 1.0
                    k += 1
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos))
                ground_count += 1
                ypos = float(initial_ypos)
                xpos = advance_x(design, xpos, ypos, x_margin)

        # Caso en que no se duplica        
        else:
            # Si el resonador actual es SERIE
            if current_COM_type == "series":
                xpos = advance_x(design, xpos, ypos, x_margin)

            # Si el resonador actual es SHUNT
            else:
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos))
                ground_count += 1
                ypos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin)

        current_COM_type = "series" if current_COM_type == "shunt" else "shunt"
        num_COM += 1

    # OUTPUT MATCHING NETWORK (Renombrados con _COM)
    xpos = advance_x(design, xpos, ypos, x_margin)

    if matching_network == "0.0":
        # INDUCTANCE TERMINATION - Add inductor
        if endCOM_type == "series":
            # Bobina en shunt (lfini2)
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_COM", (xpos, ypos), lfini2 + "H", -90.0)
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

        else:
            # Bobina en serie (lfini2)
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_COM", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0 # Sumamos 1.0 por el tamaño del componente
            xpos = advance_x(design, xpos, ypos, x_margin)

    else:
        # CL/LC MATCHING NETWORK - Add the matching network for the output
        if mntype1 == "s":
            # Bobina Serie (lfini1) seguida de Condensador Shunt (Cfini2)
            if float(lfini1) > 0.0:
                instantiate_rflib_element(design, "L", "L_output1_COM", (xpos, ypos), lfini1 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

            if float(cfini2) > 0.0:
                instantiate_rflib_element(design, "C", "C_output2_COM", (xpos, ypos), cfini2 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

        else:
            # Condensador Shunt (Cfini1) seguido de Bobina Serie (lfini2)
            if float(cfini1) > 0.0:
                instantiate_rflib_element(design, "C", "C_output1_COM", (xpos, ypos), cfini1 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output2_COM", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

    # TermG2
    instantiate_term_g(design, f"TermG{initial_TermG+1}", initial_TermG+1, (xpos, ypos))

    return

def build_ladder_filter_circuit_busbar_COM(design: db.Design, initial_xpos: int, initial_ypos: int, initial_TermG: int, parameters: dict, list_COM: list[COM], library_name: str) -> None:
    # READ Basic Ladder parameters
    order = int(parameters["norder_ini"])
    startCOM_type = parameters["typeseriesshunt_ini"]
    endCOM_type = ""

    # Determine the type of the last COM based on the order and the type of the first COM
    if order % 2 == 0:
        endCOM_type = "shunt" if startCOM_type == "series" else "series"
    else:
        endCOM_type = "series" if startCOM_type == "series" else "shunt"

    # READ Matching network parameters
    matching_network = parameters["matching_network"]
    mntype1 = parameters["mntype1"]
    input_l = parameters["input_l"]
    lfini1 = parameters["lfini1"]
    lfini2 = parameters["lfini2"]
    cfini1 = parameters["cfini1"]
    cfini2 = parameters["cfini2"]
    
    # Grid position parameters
    xpos = initial_xpos
    ypos = initial_ypos

    x_margin = 1.5
    y_margin = 1.5

    num_COM = 0
    ground_count = 1  # Contador dedicado para tierras únicas (G1, G2, G3...)

    # =========================================== Ladder Filter of Lossy COMs ===========================================
    instantiate_term_g(design, f"TermG{initial_TermG}", initial_TermG, (xpos, ypos))

    # INPUT MATCHING NETWORK (Renombrados con _busbarCOM)
    if startCOM_type == "series":
        d = Decimal(input_l)
        if d.adjusted() > -10:
            xpos = advance_x(design, xpos, ypos, x_margin)
            instantiate_rflib_element(design, "L", "L_input_busbarCOM", (xpos, ypos), input_l + "H", -90.0)
            instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos - 1.0))
            ground_count += 1
        xpos = advance_x(design, xpos, ypos, x_margin)
    else:
        xpos = advance_x(design, xpos, ypos, x_margin)
        instantiate_rflib_element(design, "L", "L_input_busbarCOM", (xpos, ypos), input_l + "H", 0.0)
        xpos += 1
        xpos = advance_x(design, xpos, ypos, x_margin) # Sumamos 1.0 por el tamaño del inductor

    ypos = initial_ypos

    # ÚNICO BUCLE COM LADDER (Maneja el primero y todos los demás)
    current_COM_type = startCOM_type
    while num_COM < len(list_COM):
        xpos = advance_x(design, xpos, ypos, x_margin)

        angle_COM = 0.0 if current_COM_type == "series" else -90.0

        xpos, ypos = instantiate_busbar_and_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
        
        if current_COM_type == "shunt" and not list_COM[num_COM].name.endswith("_1s"):
            instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos))
            ground_count += 1

        duplicate = False

        if list_COM[num_COM].name.endswith("_1s"):
            duplicate = True
            if current_COM_type == "series":
                xpos = advance_x(design, xpos, ypos, x_margin)
                angle_COM = 0.0
            else:
                design.add_wire([PointF(xpos, ypos), PointF(xpos, ypos - y_margin)])
                ypos -= y_margin
                ground_count += 1
                angle_COM = -90.0

        elif list_COM[num_COM].name.endswith("_1p"):
            duplicate = True
            if current_COM_type == "series":
                xpos -= 1.0
                design.add_wire([PointF(xpos, ypos), PointF(xpos, ypos - y_margin*2)])
                design.add_wire([PointF(xpos + 1.0, ypos), PointF(xpos + 1.0, ypos - y_margin)])
                ypos -= y_margin*2
                angle_COM = 0.0
            else:
                ypos += 2.0
                xpos = advance_x(design, xpos, ypos, x_margin*2)
                advance_x(design, xpos - x_margin*2, ypos - 2.0, x_margin*2) # Wire inferior
                angle_COM = -90.0

        # Instanciamos el resonador duplicado
        if duplicate:
            num_COM += 1
            xpos, ypos = instantiate_busbar_and_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))

            if list_COM[num_COM].name.endswith("_1s") and current_COM_type == "shunt":
                    instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos))

        ypos = initial_ypos
        xpos = advance_x(design, xpos, ypos, x_margin)
        num_COM += 1
        current_COM_type = "shunt" if current_COM_type == "series" else "series"

    # OUTPUT MATCHING NETWORK (Renombrados con _COM)
    xpos = advance_x(design, xpos, ypos, x_margin)

    if matching_network == "0.0":
        # INDUCTANCE TERMINATION - Add inductor
        if endCOM_type == "series":
            # Bobina en shunt (lfini2)
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_busbarCOM", (xpos, ypos), lfini2 + "H", -90.0)
                instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

        else:
            # Bobina en serie (lfini2)
            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output_busbarCOM", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0 # Sumamos 1.0 por el tamaño del componente
            xpos = advance_x(design, xpos, ypos, x_margin)

    else:
        # CL/LC MATCHING NETWORK - Add the matching network for the output
        if mntype1 == "s":
            # Bobina Serie (lfini1) seguida de Condensador Shunt (Cfini2)
            if float(lfini1) > 0.0:
                instantiate_rflib_element(design, "L", "L_output1_busbarCOM", (xpos, ypos), lfini1 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

            if float(cfini2) > 0.0:
                instantiate_rflib_element(design, "C", "C_output2_busbarCOM", (xpos, ypos), cfini2 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

        else:
            # Condensador Shunt (Cfini1) seguido de Bobina Serie (lfini2)
            if float(cfini1) > 0.0:
                instantiate_rflib_element(design, "C", "C_output1_busbarCOM", (xpos, ypos), cfini1 + "F", -90.0)
                instantiate_ground(design, f"G{ground_count}_busbarCOM", (xpos, ypos - 1.0))
                ground_count += 1
            xpos = advance_x(design, xpos, ypos, x_margin*2)

            if float(lfini2) > 0.0:
                instantiate_rflib_element(design, "L", "L_output2_busbarCOM", (xpos, ypos), lfini2 + "H", 0.0)
                xpos += 1.0
            xpos = advance_x(design, xpos, ypos, x_margin)

    # TermG2
    instantiate_term_g(design, f"TermG{initial_TermG+1}", initial_TermG+1, (xpos, ypos))

    return

def create_Schematic_debugging(workspace_path: str, library_name: str, frequency_plan: FrequencyPlan, 
                               list_BVD: list[BVD], list_COM: list[COM]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_DEBUG}:schematic")
    design = db.open_design(f"{library_name}:{CELL_DEBUG}:schematic")
    
    # Sweep parameters
    fstart = frequency_plan.fstart
    fstop = frequency_plan.fstop
    npoints = frequency_plan.Nsteps
    
    # Grid positon parameters
    xpos = 0.0
    ypos = 0.0
    num_BVD = 0
    num_COM = 0

    with Transaction(design) as transaction:
        # =========================================== BVDs for debugging ===========================================
        idx = 1
        while num_BVD < len(list_BVD):
            # Pongo un TermG según index
            instantiate_term_g(design, f"TermG{idx}", idx, (xpos, ypos))
            xpos = advance_x(design, xpos, ypos, 1.0)

            # Pongo el elemento BVD/COM
            instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, 0.0, (xpos, ypos))
            xpos += 1

            if list_BVD[num_BVD].name.endswith("_1s"):
                num_BVD += 1
                xpos = advance_x(design, xpos, ypos, 1.0)
                instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, 0.0, (xpos, ypos))    
                xpos += 1

            elif list_BVD[num_BVD].name.endswith("_1p"):
                xpos -= 1
                num_BVD += 1
                ypos = advance_y(design, xpos, ypos, -2.0)
                instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, 0.0, (xpos, ypos))
                xpos += 1
                ypos = advance_y(design, xpos, ypos, 2.0) - 2.0

            # Pongo el terminal ground según index
            instantiate_ground(design, f"G{idx}", (xpos, ypos))

            # Recolocamos el pointer más adelante
            xpos += 2
            ypos = 0.0
            num_BVD += 1
            idx += 1

        # =========================================== COMs for debugging ===========================================
        xpos = 0.0
        ypos = -5.0
        while num_COM < len(list_COM):
            # Pongo un TermG según index
            instantiate_term_g(design, f"TermG{idx}", idx, (xpos, ypos))
            xpos = advance_x(design, xpos, ypos, 1.0)

            # Pongo el elemento BVD/COM
            instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, 0.0, (xpos, ypos))
            xpos += 1

            if list_COM[num_COM].name.endswith("_1s"):
                num_COM += 1
                xpos = advance_x(design, xpos, ypos, 1.0)
                instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, 0.0, (xpos, ypos))
                xpos += 1

            elif list_COM[num_COM].name.endswith("_1p"):
                xpos -= 1
                num_COM += 1
                ypos = advance_y(design, xpos, ypos, -2.0)
                instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, 0.0, (xpos, ypos))
                xpos += 1
                ypos = advance_y(design, xpos, ypos, 2.0) - 2.0

            # Pongo el terminal ground según index
            instantiate_ground(design, f"G{idx}", (xpos, ypos))

            # Recolocamos el pointer más adelante
            xpos += 2
            ypos = -5.0
            num_COM += 1
            idx += 1

        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': str(fstart), 'fstop': str(fstop), 'npoints': str(npoints)})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])


        # =========================================== S parameters simulation ===========================================
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 3.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        inst.parameters["Step"].value = "(fstop-fstart)/npoints Hz"
        inst.parameters["Sort"].value = "LINEAR START STEP "
        inst.parameters["CalcY"].value = "yes"
        inst.parameters["Freq"].value = " "
        inst.update_item_annotation()


        # FINISH
        transaction.commit()

    design.save_design()

    # =========================================== EXTRAER EL NETLIST Y SIMULAR ===========================================
    netlist = design.generate_netlist()

    # Definimos dónde queremos que se guarde el archivo de datos (.ds)
    output_dir = os.path.join(workspace_path, "data")
    os.makedirs(output_dir, exist_ok=True)

    simulator = eda_ads.CircuitSimulator()
    
    # Esto bloqueará la ejecución de Python hasta que la simulación termine
    simulator.run_netlist(netlist, output_dir=output_dir)

    # Limpiamos
    design = None

    return

# ===================================== CREATION OF DDS FILES FUNCTIONS =====================================

def create_DDS_filters_schematic(workspace_path: str) -> None:
    # ========= 1) Crear el documento DDS =========
    dataset_name = CELL_FILTER
    doc = dds.new_dds_file(dataset_name, workspace_path)
    
    # ========= 2) Configurar la página =========
    page = doc.pages[0]
    page.name = "S_Parameters"

    # Definimos constantes de diseño para consistencia
    plot_width = 4000
    plot_height = 3000
    margin_x = 600  # Espacio entre los dos gráficos

    # ========= 3) Crear Plot 1 (S11 y S33) =========
    traces_plot1 = [
        f"dB({dataset_name}..S(1,1))", 
        f"dB({dataset_name}..S(3,3))", 
        f"dB({dataset_name}..S(5,5))", 
        f"dB({dataset_name}..S(7,7))"
    ]
    plot1 = page.add_plot((plot_width, plot_height), traces_plot1, "Return Loss")
    # Lo movemos explícitamente al origen (opcional, suele ser el default)
    plot1.move(dds.Point(0, 0))

    # ========= 4) Crear Plot 2 (S21 y S43) =========
    traces_plot2 = [
        f"dB({dataset_name}..S(2,1))",  
        f"dB({dataset_name}..S(4,3))",
        f"dB({dataset_name}..S(6,5))",
        f"dB({dataset_name}..S(8,7))"
    ]
    plot2 = page.add_plot((plot_width, plot_height), traces_plot2, "Insertion Loss")

    # ========= 5) Posicionar Plot 2 con lógica de la segunda función =========
    # Calculamos la posición: ancho del primero + margen
    x_pos_plot2 = plot_width + margin_x
    plot2.move(dds.Point(x_pos_plot2, 0))

    # ========= 6) Guardar =========
    dds_file_path = os.path.join(workspace_path, f"{dataset_name}.dds")
    doc.save(dds_file_path)
    dds.close_dds_file(doc)

def create_DDS_debugging(workspace_path: str, order: int, startType: str) -> None:
    # ========= 1) Crear el documento DDS =========
    dataset_name = CELL_DEBUG  # Asegúrate de que CELL_DEBUG esté definida
    doc = dds.new_dds_file(dataset_name, workspace_path)
    
    # ========= 2) Configurar la página =========
    page = doc.pages[0]
    page.name = "S_Parameters"

    # Definimos el tamaño de los plots, márgenes y límite de columnas
    plot_width = 4000
    plot_height = 3000
    margin_x = 500  # Espaciado horizontal
    margin_y = 500  # Espaciado vertical entre filas
    max_cols = 3    # Máximo número de plots por fila

    # --- CREACIÓN DE PLOTS ---
    currentType = startType
    for i in range(order):
        port_num = i + 1  # Empieza en 1 y llega hasta 'order'
        
        # Calcular la fila y columna actual en base al límite de 3 columnas
        row = i // max_cols
        col = i % max_cols
        
        # Calcular coordenadas X e Y
        x_pos = col * (plot_width + margin_x)
        y_pos = row * (plot_height + margin_y)
        
        traces = [
            f"dB({dataset_name}..Y({port_num},{port_num}))",
            f"dB({dataset_name}..Y({port_num+order},{port_num+order}))"
        ]
        
        # Nota: Si add_plot en tu versión de ADS espera un único string para el título,
        # te recomiendo cambiar esto a algo como: f"Y({port_num},{port_num}) BVD vs COM"
        title = f"Admitance Comparison of {currentType}_{i+1}"
        plot = page.add_plot((plot_width, plot_height), traces, title)
        plot.move(dds.Point(x_pos, y_pos))

        currentType = "series" if currentType == "shunt" else "shunt"

    # ========= 3) Guardar (y DEJAR ABIERTO) =========
    dds_file_path = os.path.join(workspace_path, f"{dataset_name}.dds")
    doc.save(dds_file_path)
    dds.close_dds_file(doc)

    return

def extract_data_debugging(workspace_path: str, order: int,list_BVD: list[BVD], list_COM: list[COM]) -> tuple[list[BVD], list[COM]]:
    dataset_name = CELL_DEBUG

    # Extract data
    output_dir = os.path.join(workspace_path, "data")
    output_data = dataset.open(Path(os.path.join(output_dir, f"{dataset_name}.ds")))
    dataf = output_data["SP1.SP"].to_dataframe().reset_index()

    print_data_txt(output_data, output_dir, dataset_name)
    
    idx = 1
    f = dataf["freq"]
    for bvd, com in zip(list_BVD, list_COM):
        bvd.f = f
        com.f = f
        bvd.Y = dataf[f"Y[{idx},{idx}]"]
        com.Y = dataf[f"Y[{idx+order},{idx+order}]"]
        idx += 1

    return list_BVD, list_COM

def extract_data_filter_COM(workspace_path: str) -> FilterResponse:
    dataset_name = CELL_FILTER

    # Extract data
    output_dir = os.path.join(workspace_path, "data")
    output_data = dataset.open(Path(os.path.join(output_dir, f"{dataset_name}.ds")))
    dataf = output_data["SP1.SP"].to_dataframe().reset_index()

    print_data_txt(output_data, output_dir, dataset_name)
    
    f = dataf["freq"]
    y = dataf[f"S[{COM_FILTER_STARTING_PIN+1},{COM_FILTER_STARTING_PIN}]"]

    filter_response = FilterResponse(y, f)

    return filter_response

def extract_data_filter_BVD(workspace_path: str) -> FilterResponse:
    dataset_name = CELL_FILTER

    # Extract data
    output_dir = os.path.join(workspace_path, "data")
    output_data = dataset.open(Path(os.path.join(output_dir, f"{dataset_name}.ds")))
    dataf = output_data["SP1.SP"].to_dataframe().reset_index()

    print_data_txt(output_data, output_dir, dataset_name)
    
    f = dataf["freq"]
    y = dataf[f"S[{BVD_FILTER_STARTING_PIN+1},{BVD_FILTER_STARTING_PIN}]"]

    filter_response = FilterResponse(y, f)

    return filter_response

def print_data_txt(output_data: any, output_dir: any, dataset_name: any) -> None:
    # ==========================================
    # VOLCAR CONTENIDO DEL DATASET A UN .TXT
    # ==========================================
    txt_file_path = os.path.join(output_dir, f"{dataset_name}_debug.txt")
    
    with open(txt_file_path, "w") as f:
        f.write(f"=== CONTENIDO DEL DATASET: {dataset_name}.ds ===\n\n")
        
        # Obtenemos los nombres de las variables guardadas en el dataset
        try:
            # Forma estándar en la API de Keysight
            variable_names = output_data.keys() 
        except AttributeError:
            # Por si en tu versión específica se accede como un diccionario de otra forma
            variable_names = [v for v in dir(output_data) if not v.startswith("_")]

        for var_name in variable_names:
            f.write(f"Variable: {var_name}\n")
            f.write("-" * 50 + "\n")
            
            try:
                # Extraemos los datos matemáticos de esa variable
                data_value = output_data[var_name]
                
                # Si es una variable compleja (como los Parámetros S), la pasamos a tabla
                if hasattr(data_value, 'to_dataframe'):
                    df = data_value.to_dataframe()
                    f.write(df.to_string() + "\n")
                else:
                    # Si es un valor simple (un número o string)
                    f.write(str(data_value) + "\n")
            except Exception as e:
                f.write(f"  [!] No se pudo leer el valor de esta variable: {e}\n")
                
            f.write("\n" + "=" * 50 + "\n\n")
            
    return

# ===================================== CREATION OF LAYOUT FUNCTIONS =====================================
def create_busbars_layout_and_symbol(library: de.Library, library_name: str, com: COM) -> None:
    assert de.version() >= 630

    design = db.create_layout(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:layout")
    design = db.open_design(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:layout")

    db.StringProp.create(design, "SIM_CONTROLLER_DESIGN", f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:emSetup")
    cond = LayerId.create_layer_id_from_library(library, "cond", "drawing")

    # --- ESCALADO A MICRAS (um) ---
    d_um = com.d * 1e6
    dx_um = com.digitsN * d_um                  
    aperture_um = (com.Ap * d_um) + d_um        
    dy_um = d_um * 10                           
    dx2_um = dx_um * 0.1                        
    dy2_um = d_um * 5                           

    # --- CREACIÓN DE REDES ---
    # Red 1 para la barra superior (P1 y P3)
    net_top = design.add_net("NET_TOP")
    
    # Red 2 para la barra inferior (P2 y P4)
    net_bottom = design.add_net("NET_BOTTOM")

    # --- DIBUJO DE GEOMETRÍAS Y ASIGNACIÓN DE NETS ---
    # Barra superior
    r1 = design.add_rectangle(cond, PointF(0, 0), PointF(dx_um, dy_um))
    r1.net = net_top
    r2 = design.add_rectangle(cond, PointF(dx_um/2 - dx2_um/2, dy_um), 
                                    PointF(dx_um/2 + dx2_um/2, dy_um + dy2_um))
    r2.net = net_top

    # Barra inferior
    r3 = design.add_rectangle(cond, PointF(0, -aperture_um), PointF(dx_um, -aperture_um - dy_um))
    r3.net = net_bottom
    r4 = design.add_rectangle(cond, PointF(dx_um/2 - dx2_um/2, -aperture_um - dy_um), 
                                    PointF(dx_um/2 + dx2_um/2, -aperture_um - dy_um - dy2_um))
    r4.net = net_bottom

    # --- PUERTOS Y PINES ---
    # Barra superior (comparten net_top)
    term1 = design.add_term(net_top, "P1")
    shape1 = design.add_dot(cond, loc=PointF(dx_um/2, dy_um + dy2_um))
    design.add_pin(term1, shape1, angle=90.0, add_annot=False)

    term3 = design.add_term(net_top, "P3")
    shape3 = design.add_dot(cond, loc=PointF(dx_um/2, 0))
    design.add_pin(term3, shape3, angle=-90.0, add_annot=False)

    # Barra inferior (comparten net_bottom)
    term2 = design.add_term(net_bottom, "P2")
    shape2 = design.add_dot(cond, loc=PointF(dx_um/2, -aperture_um - dy_um - dy2_um))
    design.add_pin(term2, shape2, angle=-90.0, add_annot=False)

    term4 = design.add_term(net_bottom, "P4")
    shape4 = design.add_dot(cond, loc=PointF(dx_um/2, -aperture_um))
    design.add_pin(term4, shape4, angle=90.0, add_annot=False)

    design.save_design()
    design = None

    # ========= 2) Symbol view =========
    assert de.version() >= 630

    design = db.create_symbol(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:symbol")
    design = db.open_design(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:symbol")

    with Transaction(design) as transaction:
        # Properties
        db.StringProp.create(design, "SymbolGenSettings", '0,2,"layout",0,0,"1","dot",0')

        # Terms
        net = design.add_net("P1")
        term = design.add_term(net, "P1")
        shape = design.add_dot(db.LayerId(229), loc=PointF(0.0, 0.0))
        pin = design.add_pin(term, shape, angle=-180.0, add_annot=False)

        net = design.add_net("P2")
        term = design.add_term(net, "P2")
        shape = design.add_dot(db.LayerId(229), loc=PointF(2.0, 0.0))
        pin = design.add_pin(term, shape, add_annot=False)

        net = design.add_net("P3")
        term = design.add_term(net, "P3")
        shape = design.add_dot(db.LayerId(229), loc=PointF(0.5, 0.0))
        pin = design.add_pin(term, shape, add_annot=False)

        net = design.add_net("P4")
        term = design.add_term(net, "P4")
        shape = design.add_dot(db.LayerId(229), loc=PointF(1.5, 0.0))
        pin = design.add_pin(term, shape, angle=-180.0, add_annot=False)

        # Shapes
        points = [PointF(x=0.5, y=-1.375), PointF(x=0.5, y=1.375), PointF(x=0.25, y=1.375), PointF(x=0.25, y=-1.375)]
        shape = design.add_polygon(db.LayerId(1), polygon=points, arc_resolution=5.0)
        points = [PointF(x=0.25, y=-0.375), PointF(x=0.25, y=0.375), PointF(x=0.0, y=0.375), PointF(x=0.0, y=-0.375)]
        shape = design.add_polygon(db.LayerId(1), polygon=points, arc_resolution=5.0)
        points = [PointF(x=1.75, y=0.375), PointF(x=1.75, y=-0.375), PointF(x=2.0, y=-0.375), PointF(x=2.0, y=0.375)]
        shape = design.add_polygon(db.LayerId(1), polygon=points, arc_resolution=5.0)
        points = [PointF(x=1.5, y=1.375), PointF(x=1.5, y=-1.375), PointF(x=1.75, y=-1.375), PointF(x=1.75, y=1.375)]
        shape = design.add_polygon(db.LayerId(1), polygon=points, arc_resolution=5.0)

        shape = design.add_text(db.LayerId(237, 244), "P1", PointF(0.0375, -0.00625), "Arial For CAE", 0.06875, is_drafting=False)
        shape = design.add_text(db.LayerId(237, 244), "P2", PointF(1.875, -0.00625), "Arial For CAE", 0.06875, is_drafting=False)
        shape = design.add_text(db.LayerId(237, 244), "P4", PointF(1.5375, -0.00625), "Arial For CAE", 0.06875, is_drafting=False)
        shape = design.add_text(db.LayerId(237, 244), "P3", PointF(0.38125, -0.00625), "Arial For CAE", 0.06875, is_drafting=False)

        transaction.commit()

    design.save_design()
    design = None


    return

def create_smos_substrate(library: de.Library, subst_name: str = "smos_substrate") -> subst.Substrate:
    """
    Construye el sustrato SMOS en la librería activa.
    Requiere que los materiales 'Copper', 'Subst_1', 'SiO2' y 'Silicio' 
    existan previamente en la tecnología/workspace.
    """
    # 1. Recrear el sustrato si ya existía
    if subst.substrate_exists(library, subst_name):
        subst.delete_substrate(library, subst_name)
        
    s = subst.create_substrate(library, subst_name)

    # 2. Obtener rol de conductor
    try:
        role_conductor = de.ProcessRole.CONDUCTOR
    except AttributeError:
        from keysight.ads.de._pde.tech import ProcessRole
        role_conductor = ProcessRole.CONDUCTOR

    # ---------------------------------------------------------------------
    # CAPA CONDUCTORA: cond (Copper, 200 nm)
    # ---------------------------------------------------------------------
    cond_layer = s.insert_layer(index_or_interface=1, process_role=role_conductor)
    cond_layer.material_name = "Copper"
    cond_layer.thickness_expr = '200'
    cond_layer.thickness_unit = subst.Unit.NANOMETER
    cond_layer.precedence = 1
    cond_layer.sheet = False
    cond_layer.is_above = True
    cond_layer.model_type = cond_layer.ModelType.USE_DEFAULT
    cond_layer.layer_number = 1
    
    if hasattr(cond_layer, 'layer_name'):
        cond_layer.layer_name = "cond"
    elif hasattr(cond_layer, 'name'):
        cond_layer.name = "cond"

    # ---------------------------------------------------------------------
    # CAPA DIELÉCTRICA 1: Subst_1 (LiNbO3, 500 nm)
    # ---------------------------------------------------------------------
    s.insert_material_and_interface_below(material_index=0)
    linbo3_layer = s.materials[1]
    linbo3_layer.material_name = "LiNbO3"
    linbo3_layer.thickness_expr = '500'
    linbo3_layer.thickness_unit = subst.Unit.NANOMETER

    # ---------------------------------------------------------------------
    # CAPA DIELÉCTRICA 2: SiO2 (250 nm)
    # ---------------------------------------------------------------------
    s.insert_material_and_interface_below(material_index=0)
    sio2_layer = s.materials[1]
    sio2_layer.material_name = "SiO2"
    sio2_layer.thickness_expr = '250'
    sio2_layer.thickness_unit = subst.Unit.NANOMETER

    # ---------------------------------------------------------------------
    # CAPA DIELÉCTRICA 3: Silicio (100 µm)
    # ---------------------------------------------------------------------
    s.insert_material_and_interface_below(material_index=0)
    silicio_layer = s.materials[1]
    silicio_layer.material_name = "Si"
    silicio_layer.thickness_expr = '100'
    silicio_layer.thickness_unit = subst.Unit.MICRON

    # Guardar en librería
    s.save_substrate()
    print(f"[SUCCESS] Sustrato '{subst_name}' compilado correctamente.")
    return s

# ===================================== SCHEMATIC ORIENTED FUNCTIONS =====================================

def instantiate_rflib_element(design: object, element_type: str, name: str, origin: tuple[float, float], 
                              value: str, angle: float = 0.0) -> None:
    component_path = f"ads_rflib:{element_type}"
    inst = design.add_instance(component_path, name=name, origin=origin, angle=angle)
    inst.parameters[element_type].value = value
    inst.update_item_annotation()

    return

def instantiate_BVD_in_schematic(design: object, library_name: str, list_BVD: list[BVD], 
                                 num_BVD: int, angle_BVD: float, origin: tuple[float, float]) -> None:
    bvd = list_BVD[num_BVD]
    inst = design.add_instance((library_name, CELL_BVD_LOSSY, "symbol"), origin=origin, name=bvd.name, angle=angle_BVD)
    inst.parameters["Cp"].value = str(bvd.cp)
    inst.parameters["Ca"].value = str(bvd.ca)
    inst.parameters["La"].value = str(bvd.la)
    inst.parameters["Ladd_ser"].value = str(bvd.ladd_ser if bvd.ladd_ser != 0.0 else 1e-20)
    inst.parameters["Ladd_shu"].value = str(bvd.ladd_shu if bvd.ladd_shu != 0.0 else 1e-20)
    inst.parameters["Cadd_ser"].value = str(bvd.cadd_ser if bvd.cadd_ser != 0.0 else 1e-20)
    inst.parameters["Cadd_shu"].value = str(bvd.cadd_shu if bvd.cadd_shu != 0.0 else 1e-20)
    inst.parameters["Ladd_ground"].value = str(bvd.ladd_ground if bvd.ladd_ground != 0.0 else 1e-20)
    inst.parameters["Rs"].value = str(bvd.rs)
    inst.parameters["Rp"].value = str(bvd.rp)
    inst.parameters["Ql"].value = str(bvd.ql)
    inst.parameters["Qc"].value = str(bvd.qc)
    inst.parameters["Qa"].value = str(bvd.qa)
    inst.update_item_annotation()
    return

def instantiate_COM_in_schematic(design: object, library_name: str, list_COM: list[COM], 
                                 num_COM: int, angle_COM: float, origin: tuple[float, float]) -> None:
    com = list_COM[num_COM]
    inst = design.add_instance((library_name, CELL_COM_LOSSY, "symbol"), origin=origin, name=com.name, angle=angle_COM)
    inst.parameters["d"].value = str(com.d)
    inst.parameters["d_refl"].value = str(com.dR)
    inst.parameters["Ap"].value = str(com.Ap)
    inst.parameters["DigitsActiveIDT"].value = str(com.digitsN)
    inst.parameters["DigitsReflector"].value = str(com.digitsNR)
    inst.parameters["alpha"].value = str(com.alpha)
    inst.parameters["vp"].value = str(com.constants.vp)
    inst.parameters["k11_real"].value = str(com.constants.k11_real)
    inst.parameters["alphaC"].value = str(com.constants.k11_att_cnst)
    inst.parameters["k12"].value = str(com.constants.k12)
    inst.parameters["eps_r"].value = str(com.constants.eps_r)
    inst.parameters["eps_0"].value = str(com.constants.eps_0)
    inst.parameters["duty"].value = str(com.constants.duty)
    inst.update_item_annotation()

    return

def instantiate_busbar_and_COM_in_schematic(design: object, library_name: str, list_COM: list[COM], 
                                 num_COM: int, angle_COM: float, origin: tuple[float, float]) -> tuple[float, float]:
    com = list_COM[num_COM]

    # Los layouts de los duplicados son del nombre del primer COM
    if (com.name.endswith("_2s") or com.name.endswith("_2p")):
        busbar_name = list_COM[num_COM-1].name
    else:
        busbar_name = list_COM[num_COM].name
        
    # 1. Instanciar la barra colectora
    design.add_instance((library_name, f"{CELL_BUSBAR_LAYOUT}_{busbar_name}", "symbol"), origin=origin, name=f"{com.name}_busbar", angle=angle_COM)
    
    # 2. Sumar coordenadas X e Y correctamente según el ángulo
    if angle_COM == 0.0:
        com_position = (origin[0] + 0.5, origin[1])
        final_position = (origin[0] + 2.0, origin[1])
    else:
        com_position = (origin[0], origin[1] - 0.5)
        final_position = (origin[0], origin[1] - 2.0)

    # 3. Instanciar COM
    inst = design.add_instance((library_name, CELL_COM_LOSSY, "symbol"), origin=com_position, name=f"internal_{com.name}", angle=angle_COM)
    inst.parameters["d"].value = str(com.d)
    inst.parameters["d_refl"].value = str(com.dR)
    inst.parameters["Ap"].value = str(com.Ap)
    inst.parameters["DigitsActiveIDT"].value = str(com.digitsN)
    inst.parameters["DigitsReflector"].value = str(com.digitsNR)
    inst.parameters["alpha"].value = str(com.alpha)
    inst.parameters["vp"].value = str(com.constants.vp)
    inst.parameters["k11_real"].value = str(com.constants.k11_real)
    inst.parameters["alphaC"].value = str(com.constants.k11_att_cnst)
    inst.parameters["k12"].value = str(com.constants.k12)
    inst.parameters["eps_r"].value = str(com.constants.eps_r)
    inst.parameters["eps_0"].value = str(com.constants.eps_0)
    inst.parameters["duty"].value = str(com.constants.duty)
    inst.update_item_annotation()

    return final_position

def advance_x(design, xpos: float, ypos: float, dx: float) -> float:
    design.add_wire([PointF(xpos, ypos), PointF(xpos + dx, ypos)])
    return xpos + dx

def advance_y(design, xpos: float, ypos: float, dy: float) -> float:
    design.add_wire([PointF(xpos, ypos), PointF(xpos, ypos + dy)])
    return ypos + dy

def instantiate_ground(design, name: str, origin: tuple[float, float]) -> None:
    design.add_instance("ads_rflib:GROUND", name=name, origin=origin, angle=-90.0, ads_annot=False)

def instantiate_term_g(design, name: str, num: int, origin: tuple[float, float]) -> None:
    inst = design.add_instance("ads_simulation:TermG", name=name, origin=origin, angle=-90.0)
    inst.parameters["Num"].value = str(num)
    inst.update_item_annotation()