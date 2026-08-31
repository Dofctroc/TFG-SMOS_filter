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

from bvd_com_computations import BVD
from bvd_com_computations import COM
from bvd_com_computations import FilterResponse

FORCE_RECREATE = True

CELL_BVD_LOSSY = "BVD_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_COM_LOSSY = "COM_Lossy_symb"       # celda jerárquica (schematic+symbol)
CELL_FILTER_BVD = "Ladder_Filter_BVD"   # celda jerárquica (schematic)
CELL_FILTER_COM = "Ladder_Filter_COM"   # celda jerárquica (schematic)
CELL_FILTER = "Filters"                 # celda jerárquica (schematic)
CELL_DEBUG = "Debugging"
CELL_BUSBAR_LAYOUT = "Busbar_layout"

BVD_FILTER_STARTING_PIN = 1
COM_FILTER_STARTING_PIN = 3

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

def create_SchematicAndSymbol_lossyCOM(library: de.Library, library_name: str) -> None:
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
        inst = design.add_var_instance(name="Consts1", origin=(-9.0, 1.75))
        inst.vars.update({'duty': '0.55', 'eps0': '8.8541878176e-12', 'Z0_prima': '1'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Consts2", origin=(-9.0, -0.25))
        inst.vars.update({'Rseries': '0.1', 'Rshunt': '400000', 'alphaC': '450'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Impedance_IDT", origin=(-6.125, 3.75))
        inst.vars.update({'delta': 'k-k0', 'beta': 'sqrt((delta+k11)^2-k12^2)', 'p': '(beta-delta-k11)/k12', 'Z0': '(1-p)/(1+p)*Z0_prima', 'Z0R': '(1+p)/(1-p)*Z0_prima'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Impedance_Refl", origin=(-6.125, 2.125))
        inst.vars.update({'delta_refl': 'k-k0_refl', 'beta_refl': 'sqrt((delta_refl+k11)^2-k12^2)', 'p_refl': '(beta_refl-delta_refl-k11)/k12', 'Z0_refl': '(1-p_refl)/(1+p_refl)*Z0_prima', 'Z0R_refl': '(1+p_refl)/(1-p_refl)*Z0_prima'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Inputs", origin=(-9.0, 3.75))
        inst.vars.update({'L': '2*d', 'L_refl': '2*d_refl', 'k0': 'pi/d', 'k0_refl': 'pi/d_refl', 'k': '2*pi*freq/vp', 'N': 'DigitsActiveIDT/2', 'NR': 'DigitsReflector/2'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Vars_IDT", origin=(-6.125, 0.5))
        inst.vars.update({'theta': '(beta*N*L)/2', 'phi': '2*alpha*L*N*sqrt(Z0_prima)', 'CT': 'Ap*N*L*eps_r*eps0*exp(0.71866*tan(1.966*(duty-0.5)))'})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        param = inst.parameters[0]
        assert isinstance(param, db.ParamRepeated)
        del(param.repeats[0])

        inst = design.add_var_instance(name="Vars_Refl", origin=(-6.125, -0.625))
        inst.vars.update({'theta_refl': '(beta_refl*NR*L_refl)/2', 'phi_refl': '2*alpha*L_refl*NR*sqrt(Z0_prima)', 'CT_refl': 'Ap*NR*L_refl*eps_r*eps0*exp(0.71866*tan(1.966*(duty-0.5)))'})
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
    varD.default_value = de.db_uu.ParamItemString("d", "StdForm", str("0.1"))
    varD.is_displayed_by_default = True

    varDR = de.db_uu.ModelParam("d_refl", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varDR.default_value = de.db_uu.ParamItemString("d_refl", "StdForm", str("0.1"))
    varDR.is_displayed_by_default = True

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

    varVp = de.db_uu.ModelParam("vp", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varVp.default_value = de.db_uu.ParamItemString("vp", "StdForm", str("50"))
    varVp.is_displayed_by_default = True

    varK11 = de.db_uu.ModelParam("k11", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varK11.default_value = de.db_uu.ParamItemString("k11", "StdForm", str("50"))
    varK11.is_displayed_by_default = True

    varK12 = de.db_uu.ModelParam("k12", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varK12.default_value = de.db_uu.ParamItemString("k12", "StdForm", str("50"))
    varK12.is_displayed_by_default = True

    varEpsR = de.db_uu.ModelParam("eps_r", "Unitless", formset, de.db_uu.ModelUnitType.NO_UNIT)
    varEpsR.default_value = de.db_uu.ParamItemString("eps_r", "StdForm", str("50"))
    varEpsR.is_displayed_by_default = True

    model_def = de.db_uu.ModelDef(CELL_COM_LOSSY, CELL_COM_LOSSY)
    model_def.inst_name_prefix = "lossyCOM"
    model_def.is_sub_design = True
    model_def.parameters = [varD, varDR, varAp, varDigitsActiveIDT, varDigitsReflector, varAlpha, varVp, varK11, varK12, varEpsR]

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

def create_Schematic_ladder_filters(workspace_path: str, library_name: str, dataset_s2p_path: str, parameters: dict, list_BVD: list[BVD], list_COM: list[COM]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_FILTER}:schematic")
    design = db.open_design(f"{library_name}:{CELL_FILTER}:schematic")
    
    # Sweep parameters
    fstart = parameters["fstart1"]
    fstop = parameters["fstop1"]
    npoints = parameters["npoints1"]

    with Transaction(design) as transaction:

        # =========================================== Sparameters Data Item for Comparison ===========================================
        if dataset_s2p_path is not None:
            inst = design.add_instance("ads_simulation:TermG", name="TermG5", origin=(6.0, 3.0), angle=-90.0)
            inst.parameters["Num"].value = "5"
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
            inst = design.add_instance("ads_simulation:TermG", name="TermG6", origin=(9.0, 3.0), angle=-90.0)
            inst.parameters["Num"].value = "6"
            inst.update_item_annotation()


        # =========================================== S parameters simulation ===========================================
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 3.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        inst.parameters["Step"].value = "(fstop-fstart)/1000 Hz"
        inst.parameters["Sort"].value = "LINEAR START STEP "
        inst.parameters["CalcY"].value = "yes"
        inst.parameters["Freq"].value = " "
        inst.update_item_annotation()

        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': fstart, 'fstop': fstop, 'npoints': npoints})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])

        
        # =========================================== BVD ladder filter build ===========================================
        initial_xpos_BVD = 0
        initial_ypos_BVD = 0
        initial_TermG_BVD = BVD_FILTER_STARTING_PIN
        build_ladder_filter_circuit_BVD(design, initial_xpos_BVD, initial_ypos_BVD, initial_TermG_BVD, parameters, list_BVD, library_name)

        # =========================================== COM ladder filter build ===========================================
        initial_xpos_COM = 0
        initial_ypos_COM = -4
        initial_TermG_COM = COM_FILTER_STARTING_PIN
        build_ladder_filter_circuit_COM(design, initial_xpos_COM, initial_ypos_COM, initial_TermG_COM, parameters, list_COM, library_name)


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
    # READ Basic Ladder parameters
    order = int(parameters["norder_ini"])
    startBVD_type = parameters["typeseriesshunt_ini"]
    
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

    x_margin = 1.5
    y_margin = 1.5

    xpos = initial_xpos
    ypos = initial_ypos

    ground_count = 1
    num_BVD = 0

    # =========================================== Ladder Filter of Lossy BVDs ===========================================
    instantiate_term_g(design, f"TermG{initial_TermG}", initial_TermG, (xpos, ypos))

    # INPUT MATCHING NETWORK (Renombrados con _BVD)
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
        xpos += 1
        xpos = advance_x(design, xpos, ypos, x_margin) # Sumamos 1.0 por el tamaño del inductor

    ypos = initial_ypos

    current_BVD_type = startBVD_type
    # BVD LADDER: Único bucle para toda la escalera
    while num_BVD < len(list_BVD):
        xpos = advance_x(design, xpos, ypos, x_margin)

        angle_BVD = 0.0 if current_BVD_type == "series" else -90.0
        
        instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))

        if current_BVD_type == "shunt" and not list_BVD[num_BVD].name.endswith("_1s"):
            instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
            ground_count += 1
        
        xpos += 1.0 if current_BVD_type == "series" else 0.0
        ypos -= 1.0 if current_BVD_type == "shunt" else 0.0

        duplicate = False

        if list_BVD[num_BVD].name.endswith("_1s"):
            duplicate = True
            if current_BVD_type == "series":
                xpos = advance_x(design, xpos, ypos, x_margin)
                angle_BVD = 0.0
            else:
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos, y=ypos - y_margin)])
                ypos -= y_margin
                instantiate_ground(design, f"G{ground_count}_BVD", (xpos, ypos - 1.0))
                ground_count += 1
                angle_BVD = -90.0

        elif list_BVD[num_BVD].name.endswith("_1p"):
            duplicate = True
            if current_BVD_type == "series":
                xpos -= 1.0
                design.add_wire([PointF(x=xpos, y=ypos), PointF(x=xpos, y=ypos - y_margin)])
                design.add_wire([PointF(x=xpos + 1.0, y=ypos), PointF(x=xpos + 1.0, y=ypos - y_margin)])
                ypos -= y_margin
                angle_BVD = 0.0
            else:
                ypos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin)
                advance_x(design, xpos - x_margin, ypos - y_margin, x_margin)
                angle_BVD = -90.0

        if duplicate:
            num_BVD += 1
            instantiate_BVD_in_schematic(design, library_name, list_BVD, num_BVD, angle_BVD, (xpos, ypos))

        xpos += 1.0 if current_BVD_type == "series" and list_BVD[num_BVD-1].name.endswith(("_1p", "_1s")) else 0.0
        ypos += 1.0 if (current_BVD_type == "series" and list_BVD[num_BVD-1].name.endswith("_1p")) or (current_BVD_type == "shunt" and list_BVD[num_BVD-1].name.endswith("_1s")) else 0.0

        ypos = initial_ypos
        xpos = advance_x(design, xpos, ypos, x_margin)
        num_BVD += 1
        current_BVD_type = "shunt" if current_BVD_type == "series" else "series"

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
    
    # Grid position parameters
    xpos = initial_xpos
    ypos = initial_ypos

    x_margin = 1.5
    y_margin = 1.5

    num_COM = 0
    ground_count = 1  # Contador dedicado para tierras únicas (G1, G2, G3...)

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

    # ÚNICO BUCLE COM LADDER (Maneja el primero y todos los demás)
    current_COM_type = startCOM_type
    while num_COM < len(list_COM):
        xpos = advance_x(design, xpos, ypos, x_margin)

        angle_COM = 0.0 if current_COM_type == "series" else -90.0
        
        instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))
        
        if current_COM_type == "shunt" and not list_COM[num_COM].name.endswith("_1s"):
            instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
            ground_count += 1

        xpos += 1.0 if current_COM_type == "series" else 0.0
        ypos -= 1.0 if current_COM_type == "shunt" else 0.0

        duplicate = False

        if list_COM[num_COM].name.endswith("_1s"):
            duplicate = True
            if current_COM_type == "series":
                xpos = advance_x(design, xpos, ypos, x_margin)
                angle_COM = 0.0
            else:
                design.add_wire([PointF(xpos, ypos), PointF(xpos, ypos - y_margin)])
                ypos -= y_margin
                instantiate_ground(design, f"G{ground_count}_COM", (xpos, ypos - 1.0))
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
                ypos += 1.0
                xpos = advance_x(design, xpos, ypos, x_margin*2)
                advance_x(design, xpos - x_margin*2, ypos - 1.0, x_margin*2) # Wire inferior
                angle_COM = -90.0

        if duplicate:
            num_COM += 1
            instantiate_COM_in_schematic(design, library_name, list_COM, num_COM, angle_COM, (xpos, ypos))

        xpos += 1.0 if current_COM_type == "series" and list_COM[num_COM-1].name.endswith(("_1p", "_1s")) else 0.0
        ypos += 1.0 if (current_COM_type == "series" and list_COM[num_COM-1].name.endswith("_1p")) or (current_COM_type == "shunt" and list_COM[num_COM-1].name.endswith("_1s")) else 0.0

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

def create_Schematic_debugging(workspace_path: str, library_name: str, parameters: dict, list_BVD: list[BVD], list_COM: list[COM]) -> None:
    assert de.version() >= 630

    design = db.create_schematic(f"{library_name}:{CELL_DEBUG}:schematic")
    design = db.open_design(f"{library_name}:{CELL_DEBUG}:schematic")
    
    # Sweep parameters
    fstart = parameters["fstart1"]
    fstop = parameters["fstop1"]
    npoints = parameters["npoints1"]
    
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

            # Pongo el terminal ground según index
            instantiate_ground(design, f"G{idx}", (xpos, ypos))

            # Recolocamos el pointer más adelante
            xpos += 2
            num_BVD += 1
            idx += 1

        # =========================================== COMs for debugging ===========================================
        xpos = 0.0
        ypos = -4.0
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
            ypos = -4.0
            num_COM += 1
            idx += 1

        # Variables 
        inst = design.add_var_instance(name="VAR_Sweep", origin=(3.0, 3.0))
        inst.vars.update({'fstart': fstart, 'fstop': fstop, 'npoints': npoints})
        # Since inst.vars does not contain 'X', we need to remove the first repeat.
        assert isinstance(inst.parameters[0], db.ParamRepeated)
        del(inst.parameters[0].repeats[0])


        # =========================================== S parameters simulation ===========================================
        inst = design.add_instance("ads_simulation:S_Param", name="SP1", origin=(0.0, 3.0))
        inst.parameters["Start"].value = "fstart Hz"
        inst.parameters["Stop"].value = "fstop Hz"
        inst.parameters["Step"].value = "(fstop-fstart)/1000 Hz"
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
        f"dB({dataset_name}..S(5,5))"
    ]
    plot1 = page.add_plot((plot_width, plot_height), traces_plot1, "Return Loss")
    # Lo movemos explícitamente al origen (opcional, suele ser el default)
    plot1.move(dds.Point(0, 0))

    # ========= 4) Crear Plot 2 (S21 y S43) =========
    traces_plot2 = [
        f"dB({dataset_name}..S(2,1))",  
        f"dB({dataset_name}..S(4,3))",
        f"dB({dataset_name}..S(6,5))"
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

def extract_data_filterCOM(workspace_path: str) -> FilterResponse:
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
def create_busbars_layout(library: de.Library, library_name: str, com: COM) -> None:
    assert de.version() >= 630

    design = db.create_layout(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:layout")
    design = db.open_design(f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:layout")

    db.StringProp.create(design, "SIM_CONTROLLER_DESIGN", f"{library_name}:{CELL_BUSBAR_LAYOUT}_{com.name}:emSetup")
    cond = LayerId.create_layer_id_from_library(library, "cond", "drawing")

    # --- ESCALADO A MICRAS (um) ---
    # Convertimos com.d (metros) a micras (* 1e6)
    d_um = com.d * 1e6
    
    # Ancho del busbar proporcional al número de dígitos
    dx_um = com.digitsN * d_um                  
    
    # Apertura entre busbars en micras
    aperture_um = (com.Ap * d_um) + d_um        
    
    # Ancho (dy) y terminales (dy2) escalados proporcionalmente al diseño
    dy_um = d_um * 10                           # Altura de la barra principal
    dx2_um = dx_um * 0.1                        # Ancho de la pestaña de contacto
    dy2_um = d_um * 5                           # Largo de la pestaña de contacto

    # --- DIBUJO DE GEOMETRÍAS (Coordenadas en um) ---
    # Barra superior y su terminal
    r1 = design.add_rectangle(cond, PointF(0, 0), PointF(dx_um, dy_um))
    r2 = design.add_rectangle(cond, PointF(dx_um/2 - dx2_um/2, dy_um), 
                                    PointF(dx_um/2 + dx2_um/2, dy_um + dy2_um))

    # Barra inferior y su terminal (desplazada por la apertura)
    r3 = design.add_rectangle(cond, PointF(0, -aperture_um), PointF(dx_um, -aperture_um - dy_um))
    r4 = design.add_rectangle(cond, PointF(dx_um/2 - dx2_um/2, -aperture_um - dy_um), 
                                    PointF(dx_um/2 + dx2_um/2, -aperture_um - dy_um - dy2_um))

    # --- PUERTOS Y PINES ---
    net1 = design.add_net("P1")
    term1 = design.add_term(net1, "P1")
    shape1 = design.add_dot(cond, loc=PointF(dx_um/2, dy_um + dy2_um))
    design.add_pin(term1, shape1, angle=90.0, add_annot=False)

    net2 = design.add_net("P2")
    term2 = design.add_term(net2, "P2")
    shape2 = design.add_dot(cond, loc=PointF(dx_um/2, -aperture_um - dy_um - dy2_um))
    design.add_pin(term2, shape2, angle=-90.0, add_annot=False)

    net3 = design.add_net("P3")
    term3 = design.add_term(net3, "P3")
    shape3 = design.add_dot(cond, loc=PointF(dx_um/2, 0))
    design.add_pin(term3, shape3, angle=-90.0, add_annot=False)

    net4 = design.add_net("P4")
    term4 = design.add_term(net4, "P4")
    shape4 = design.add_dot(cond, loc=PointF(dx_um/2, -aperture_um))
    design.add_pin(term4, shape4, angle=90.0, add_annot=False)

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
    linbo3_layer.material_name = "Subst_1"
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
    silicio_layer.material_name = "Silicio"
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
    inst = design.add_instance((library_name, CELL_BVD_LOSSY, "symbol"), origin=origin, name=list_BVD[num_BVD].name, angle=angle_BVD)
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
    inst.update_item_annotation()
    return

def instantiate_COM_in_schematic(design: object, library_name: str, list_COM: list[COM], 
                                 num_COM: int, angle_COM: float, origin: tuple[float, float]) -> None:
    inst = design.add_instance((library_name, CELL_COM_LOSSY, "symbol"), origin=origin, name=list_COM[num_COM].name, angle=angle_COM)
    inst.parameters["d"].value = str(list_COM[num_COM].d)
    inst.parameters["d_refl"].value = str(list_COM[num_COM].dR)
    inst.parameters["Ap"].value = str(list_COM[num_COM].Ap)
    inst.parameters["DigitsActiveIDT"].value = str(list_COM[num_COM].digitsN)
    inst.parameters["DigitsReflector"].value = str(list_COM[num_COM].digitsNR)
    inst.parameters["alpha"].value = str(list_COM[num_COM].alpha)
    inst.parameters["vp"].value = str(list_COM[num_COM].constants.vp)
    inst.parameters["k11"].value = str(list_COM[num_COM].constants.k11)
    inst.parameters["k12"].value = str(list_COM[num_COM].constants.k12)
    inst.parameters["eps_r"].value = str(list_COM[num_COM].constants.eps_r)
    inst.update_item_annotation()
    return

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