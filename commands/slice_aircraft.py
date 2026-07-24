"""The Solid > Create command used to configure a sliced aircraft."""

from __future__ import annotations

import traceback
from collections.abc import Callable

import adsk.core
import adsk.fusion

from ..geometry import (
    AircraftBuildContext,
    AircraftDefinition,
    BuildPlacement,
    EllipticalLoftPrototypeDefinition,
)
from ..utils.events import EventSubscriptions
from ..utils.fusion import log, report_error

COMMAND_ID = "com_sliceaircraftgenerator_slice_aircraft"
COMMAND_NAME = "Slice Aircraft"
COMMAND_DESCRIPTION = "Configure a sliced-aircraft layout."
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SolidCreatePanel"
AIRCRAFT_DEFINITIONS: tuple[AircraftDefinition, ...] = (EllipticalLoftPrototypeDefinition(),)


class SliceAircraftCommand:
    """Owns the persistent command definition and toolbar control."""

    def __init__(self) -> None:
        self._subscriptions = EventSubscriptions()
        self._command_definition: adsk.core.CommandDefinition | None = None
        self._control: adsk.core.ToolbarControl | None = None
        self._active_sessions: set[_CommandSession] = set()

    def start(self) -> None:
        """Create the command definition and place it in Solid > Create."""
        app = adsk.core.Application.get()
        ui = app.userInterface

        command_definition = ui.commandDefinitions.itemById(COMMAND_ID)
        if command_definition is None:
            command_definition = ui.commandDefinitions.addButtonDefinition(
                COMMAND_ID,
                COMMAND_NAME,
                COMMAND_DESCRIPTION,
                "",  # Fusion uses its standard command icon when no asset is supplied.
            )
        self._command_definition = command_definition

        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace is None:
            raise RuntimeError("The Solid workspace is unavailable.")
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        if panel is None:
            raise RuntimeError("The Solid > Create panel is unavailable.")

        existing_control = panel.controls.itemById(COMMAND_ID)
        if existing_control is None:
            existing_control = panel.controls.addCommand(command_definition)
            existing_control.isPromoted = True
        self._control = existing_control

        handler = _CommandCreatedHandler(self)
        self._subscriptions.add(command_definition.commandCreated, handler)
        log("Slice Aircraft Generator loaded.")

    def stop(self) -> None:
        """Remove our UI and unregister the callbacks retained by this add-in."""
        self._subscriptions.clear()

        for session in tuple(self._active_sessions):
            session.dispose()
        self._active_sessions.clear()

        if self._control is not None:
            self._control.deleteMe()
            self._control = None

        if self._command_definition is not None:
            # The definition might predate this load, but it has this add-in's ID.
            self._command_definition.deleteMe()
            self._command_definition = None

        log("Slice Aircraft Generator unloaded.")

    def create_session(self, command: adsk.core.Command) -> _CommandSession:
        """Create and retain a dialog session until Fusion destroys its command."""
        session = _CommandSession(command, self._release_session)
        self._active_sessions.add(session)
        return session

    def _release_session(self, session: _CommandSession) -> None:
        self._active_sessions.discard(session)


class _CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    """Creates a fresh command session each time the toolbar button is clicked."""

    def __init__(self, owner: SliceAircraftCommand) -> None:
        super().__init__()
        self._owner = owner

    def notify(self, args: adsk.core.CommandCreatedEventArgs) -> None:
        session = self._owner.create_session(args.command)
        try:
            session.configure()
        except Exception:
            session.dispose()
            report_error("Unable to create the Slice Aircraft dialog")


class _CommandSession:
    """Retains handlers and inputs for one open instance of the command dialog."""

    def __init__(
        self, command: adsk.core.Command, release: Callable[[_CommandSession], None]
    ) -> None:
        self._command = command
        self._subscriptions = EventSubscriptions()
        self._release = release
        self._disposed = False
        self._aircraft: adsk.core.DropDownCommandInput | None = None
        self._length: adsk.core.ValueCommandInput | None = None
        self._rib_count: adsk.core.IntegerSpinnerCommandInput | None = None
        self._rib_thickness: adsk.core.ValueCommandInput | None = None

    def configure(self) -> None:
        inputs = self._command.commandInputs

        self._aircraft = inputs.addDropDownCommandInput(
            "aircraft", "Aircraft", adsk.core.DropDownStyles.TextListDropDownStyle
        )
        for index, definition in enumerate(AIRCRAFT_DEFINITIONS):
            self._aircraft.listItems.add(definition.display_name, index == 0)

        self._length = inputs.addValueInput(
            "length",
            "Length",
            "mm",
            adsk.core.ValueInput.createByString(
                f"{AIRCRAFT_DEFINITIONS[0].default_length_cm * 10:g} mm"
            ),
        )
        self._rib_count = inputs.addIntegerSpinnerCommandInput(
            "rib_count", "Rib Count", 1, 500, 1, 12
        )
        self._rib_thickness = inputs.addValueInput(
            "rib_thickness", "Rib Thickness", "mm", adsk.core.ValueInput.createByString("3 mm")
        )

        self._subscriptions.add(self._command.execute, _ExecuteHandler(self))
        self._subscriptions.add(self._command.destroy, _DestroyHandler(self))

    def execute(self) -> None:
        """Resolve the selected definition and create its native Fusion B-Rep."""
        if not all((self._aircraft, self._length, self._rib_count, self._rib_thickness)):
            raise RuntimeError("The Slice Aircraft dialog was not initialized.")

        aircraft = self._aircraft.selectedItem.name if self._aircraft.selectedItem else ""
        definition = next(
            (item for item in AIRCRAFT_DEFINITIONS if item.display_name == aircraft), None
        )
        if definition is None:
            raise RuntimeError("Select a supported aircraft definition.")

        app = adsk.core.Application.get()
        design = adsk.fusion.Design.cast(app.activeProduct)
        if design is None:
            raise RuntimeError("Open a Fusion Design before generating an aircraft.")
        placement = _placement_for_design_intent(design.designIntent)
        if design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            raise RuntimeError("Enable Capture Design History before generating an aircraft.")

        context = AircraftBuildContext(
            root_component=design.rootComponent,
            length_cm=self._length.value,
            placement=placement,
        )
        component = definition.generate(context)
        log(
            "Generated prototype component: "
            f"aircraft={aircraft}, placement={placement.value}, "
            f"target_component={component.name}, length={self._length.expression}, "
            f"rib_count={self._rib_count.value}, "
            f"rib_thickness={self._rib_thickness.expression}"
        )

    def dispose(self) -> None:
        """Release per-dialog callbacks once Fusion closes this command instance."""
        if self._disposed:
            return
        self._disposed = True
        self._subscriptions.clear()
        self._release(self)


class _ExecuteHandler(adsk.core.CommandEventHandler):
    """Runs when the user accepts the command dialog."""

    def __init__(self, session: _CommandSession) -> None:
        super().__init__()
        self._session = session

    def notify(self, args: adsk.core.CommandEventArgs) -> None:
        del args
        try:
            self._session.execute()
        except Exception:
            report_error("Slice Aircraft generation failed", traceback.format_exc())


class _DestroyHandler(adsk.core.CommandEventHandler):
    """Breaks event references when Fusion destroys the dialog command."""

    def __init__(self, session: _CommandSession) -> None:
        super().__init__()
        self._session = session

    def notify(self, args: adsk.core.CommandEventArgs) -> None:
        del args
        self._session.dispose()


def _placement_for_design_intent(design_intent: adsk.fusion.DesignIntentTypes) -> BuildPlacement:
    """Map Fusion's design intent to an explicit geometry placement mode."""
    if design_intent == adsk.fusion.DesignIntentTypes.PartDesignIntentType:
        return BuildPlacement.ROOT_COMPONENT
    if design_intent == adsk.fusion.DesignIntentTypes.HybridDesignIntentType:
        return BuildPlacement.NEW_INTERNAL_COMPONENT
    raise RuntimeError(
        "Slice Aircraft currently supports Part and Hybrid Designs. "
        "Open a Part Design or Hybrid Design to generate editable geometry."
    )
