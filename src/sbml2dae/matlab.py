from io import BytesIO
import math
from tokenize import ENCODING, NAME, OP, tokenize

from sbml2dae.dae_model import StateType


class Matlab:
    """Takes a DAE model as input and exports a matlab implementation."""

    def __init__(self, dae, output_path):
        """Inits Matlab."""
        self.dae = dae
        self.output_path = output_path

    def export_example(self):
        """Generate an example driver script."""
        filepath = self.output_path
        filepath += "/"
        filepath += self.dae.get_model_name()
        filepath += "_example.m"

        # Create and open the file to export.
        f = open(filepath, "w")

        # Function header.
        name = self.dae.get_model_name()
        f.write(f'%% Example driver script for simulating "{name}" model.\n')
        self.write_warning(f)

        # Clear and close all.
        f.write("clear all;\n")
        f.write("close all;\n")

        f.write("\n% Init model.\n")
        f.write(f"m = {name}();\n")

        # Solver options.
        f.write("\n% Solver options.\n")
        f.write("opt = odeset('AbsTol',1e-8,'RelTol',1e-8);\n")
        f.write("opt = odeset(opt,'Mass',m.M);\n")

        # Simulation time span.
        f.write("\n% Simulation time span.\n")
        f.write("tspan = [m.opts.t_init m.opts.t_end];\n")

        # Simulate.
        f.write("\n[t,x] = ode15s(@(t,x) m.ode(t,x,m.p),tspan,m.x0,opt);\n")
        f.write("out = m.simout2struct(t,x,m.p);\n")

        # Plot.
        f.write("\n% Plot result.\n")
        f.write("m.plot(out);\n")

        f.close()

        return filepath

    def export_class(self):
        """Export daeModel into a Matlab class."""
        filepath = self.output_path
        filepath += "/"
        filepath += self.dae.get_model_name()
        filepath += ".m"

        # Create and open the file to export.
        f = open(filepath, "w")

        self.write_class_header(f)
        self.write_constructor(f)
        self.write_default_parameters(f)
        self.write_initial_conditions(f)
        self.write_mass_matrix(f)
        self.write_simulation_options(f)
        self.write_ode(f)
        self.write_simout_2_struct(f)
        self.write_plot(f)

        f.write("\tend\n")
        f.write("end\n")

        f.close()

        return filepath

    def write_class_header(self, f):
        """Write into file the header of the class file."""
        # Function header.
        f.write(f"classdef {self.dae.get_model_name()}\n")
        self.write_warning(f, 1)

        # Write the properties.
        f.write("\tproperties\n")
        f.write("\t\tp      % Default model parameters.\n")
        f.write("\t\tx0     % Default initial conditions.\n")
        f.write("\t\tM      % Mass matrix for DAE systems.\n")
        f.write("\t\topts   % Simulation options.\n")
        f.write("\tend\n")
        f.write("\n")

        # Write the methods.
        f.write("\tmethods\n")

    def write_warning(self, f, tab=0):
        """Write warning comment into f."""
        tab = "\t" * tab

        f.write(f"{tab}% This file was automatically generated by OneModel.\n")
        f.write(f"{tab}% Any changes you make to it will be overwritten")
        f.write(" the next time\n")
        f.write(f"{tab}% the file is generated.\n\n")

    def write_constructor(self, f):
        """Write class constructor into f."""
        f.write(f"\t\tfunction obj = {self.dae.get_model_name()}()\n")
        f.write(f"\t\t\t%% Constructor of {self.dae.get_model_name()}.\n")
        f.write("\t\t\tobj.p    = obj.default_parameters();\n")
        f.write("\t\t\tobj.x0   = obj.initial_conditions();\n")
        f.write("\t\t\tobj.M    = obj.mass_matrix();\n")
        f.write("\t\t\tobj.opts = obj.simulation_options();\n")
        f.write("\t\tend\n")
        f.write("\n")

    def write_default_parameters(self, f):
        """Write method which returns default parameters."""
        f.write("\t\tfunction p = default_parameters(~)\n")
        f.write("\t\t\t%% Default parameters value.\n")
        f.write("\t\t\tp = [];\n")
        for item in self.dae.get_parameters():
            f.write(f'\t\t\tp.{item["id"]} = {item["value"]};\n')
        f.write("\t\tend\n")
        f.write("\n")

    def write_initial_conditions(self, f):
        """Write method which returns default initial conditions."""
        f.write("\t\tfunction x0 = initial_conditions(~)\n")
        f.write("\t\t\t%% Default initial conditions.\n")

        f.write("\t\t\tx0 = [\n")
        for item in self.dae.get_states():
            if item["type"] == StateType.ODE:
                f.write(f'\t\t\t\t{item["initialCondition"]} % {item["id"]}\n')
            elif item["type"] == StateType.ALGEBRAIC:
                f.write(f'\t\t\t\t{item["initialCondition"]}')
                f.write(f'% {item["id"]} (algebraic)\n')
        f.write("\t\t\t];\n")

        f.write("\t\tend\n")
        f.write("\n")

    def write_mass_matrix(self, f):
        """Write method which returns the mass matrix."""
        f.write("\t\tfunction M = mass_matrix(~)\n")
        f.write("\t\t\t%% Mass matrix for DAE systems.\n")

        f.write("\t\t\tM = [\n")
        m = []
        for item in self.dae.get_states():
            if item["type"] == StateType.ODE:
                m.append(1)
            elif item["type"] == StateType.ALGEBRAIC:
                m.append(0)

        i = 0
        i_max = len(m)
        while i < i_max:
            f.write("\t\t\t\t")
            f.write("0 " * i)
            f.write(f"{m[i]} ")
            f.write("0 " * (i_max - i - 1))
            f.write("\n")
            i += 1

        f.write("\t\t\t];\n")

        f.write("\t\tend\n")
        f.write("\n")

    def write_simulation_options(self, f):
        """Write method which returns the mass matrix."""
        f.write("\t\tfunction opts = simulation_options(~)\n")
        f.write("\t\t\t%% Default simulation options.\n")

        options = self.dae.get_options()
        for item in options:
            value = options.get(item, None)
            f.write(f"\t\t\topts.{item} = {value};\n")

        f.write("\t\tend\n")
        f.write("\n")

    def write_local_states(self, f):
        """Write all the states as local variables in the method."""
        # List of states that are already defined in the file.
        known_states = []
        states_num = len(self.dae.get_states())

        # Write ODE and ALGEBRAIC states.
        f.write("\t\t\t% ODE and algebraic states:\n")
        i = 1
        for state in self.dae.get_states():
            # Skip not ODE or ALGEBRAIC states.
            if not state["type"] in (StateType.ODE, StateType.ALGEBRAIC):
                continue

            f.write(f'\t\t\t{state["id"]} = x({i},:);\n')
            known_states.append(state["id"])
            i += 1
        f.write("\n")

        f.write("\t\t\t% Assigment states:\n")

        while len(known_states) != states_num:
            for state in self.dae.get_states():
                # Skip not ASSIGMENT states.
                if not state["type"] == StateType.ASSIGMENT:
                    continue

                # Skipe states that are already defined.
                if state["id"] in known_states:
                    continue

                dependencies = self.get_states(state["equation"])

                if all(elem in known_states for elem in dependencies):
                    equation = self.string2matlab(state["equation"])
                    f.write(f'\t\t\t{state["id"]} = {equation};\n')
                    known_states.append(state["id"])

        f.write("\n")

    def write_ode(self, f):
        """Write method which evaluates the ODE."""
        f.write("\t\tfunction dx = ode(~,t,x,p)\n")
        f.write("\t\t\t%% Evaluate the ODE.\n")
        f.write("\t\t\t%\n")

        # Comment arguments.
        f.write("\t\t\t% Args:\n")
        f.write("\t\t\t%\t t Current time in the simulation.\n")
        f.write("\t\t\t%\t x Array with the state value.\n")
        f.write("\t\t\t%\t p Struct with the parameters.\n")
        f.write("\t\t\t%\n")

        # Comment return.
        f.write("\t\t\t% Return:\n")
        f.write("\t\t\t%\t dx Array with the ODE.\n")
        f.write("\n")

        self.write_local_states(f)

        # Generate ODE equations.
        i = 1
        for item in self.dae.get_states():
            string = f'\t\t\t% der({item["id"]})\n'

            if item["type"] == StateType.ODE:
                equation = self.string2matlab(item["equation"])
                string += f"\t\t\tdx({i},1) = {equation};\n\n"
                f.write(string)
                i += 1

            elif item["type"] == StateType.ALGEBRAIC:
                equation = self.string2matlab(item["equation"])
                string += f"\t\t\tdx({i},1) = {equation};\n\n"
                f.write(string)
                i += 1

        f.write("\t\tend\n")

    def write_simout_2_struct(self, f):
        """Write method which calculate all the states of a simulation."""
        f.write("\t\tfunction out = simout2struct(~,t,x,p)\n")
        f.write("\t\t\t%% Convert the simulation output into")
        f.write(" an easy-to-use struct.\n")
        f.write("\n")

        f.write("\t\t\t% We need to transpose state matrix.\n")
        f.write("\t\t\tx = x';")
        f.write("\n")

        self.write_local_states(f)

        # Save the time.
        f.write("\t\t\t% Save simulation time.\n")
        f.write("\t\t\tout.t = t;")
        f.write("\n")

        # Crate ones vector.
        f.write("\n")
        f.write("\t\t\t% Vector for extending single-value states")
        f.write(" and parameters.\n")
        f.write("\t\t\tones_t = ones(size(t'));\n")
        f.write("\n")

        # Save states.
        f.write("\n\t\t\t% Save states.\n")
        for item in self.dae.get_states():
            f.write(f'\t\t\tout.{item["id"]} = ({item["id"]}.*ones_t)\';\n')
        f.write("\n")

        # Save parameters.
        f.write("\t\t\t% Save parameters.\n")
        for item in self.dae.get_parameters():
            f.write(f'\t\t\tout.{item["id"]} = (p.{item["id"]}.*ones_t)\';\n')
        f.write("\n")

        f.write("\t\tend\n")

    def write_plot(self, f):
        """Write method which plot simulation result."""
        f.write("\t\tfunction plot(~,out)\n")
        f.write("\t\t\t%% Plot simulation result.\n")

        # Get all the states we want to plot.
        states = self.dae.get_states()

        # Separate states in the different contexts.
        contexts = {}
        for state in states:
            c = state["context"]
            if contexts.get(c, None) is None:
                contexts[c] = [state]
            else:
                contexts[c].append(state)

        for context in contexts:

            states = contexts[context]

            # Calculate the size of the subplot.
            n = math.sqrt(len(states))
            x = math.ceil(n)
            y = x
            while x * (y - 1) >= len(states):
                y -= 1

            f.write(f"\t\t\tfigure('Name','{context}');\n")

            # Write subplots.
            for i in range(len(states)):
                f.write(f"\t\t\tsubplot({x},{y},{i+1});\n")
                f.write(f'\t\t\tplot(out.t, out.{states[i]["id"]});\n')
                f.write(f'\t\t\ttitle("{states[i]["id"]}");\n')
                f.write("\t\t\tylim([0, +inf]);\n")
                f.write("\t\t\tgrid on;\n")
                f.write("\n")

        f.write("\t\tend\n")

    def string2matlab(self, math_expr):
        """Parses a libSBML math string formula into a matlab expression.

        Arguments:
            math_expr: str
                Math formula obtained with libSBML.formulaToL3String()
        """
        result = ""

        parameters = []
        for item in self.dae.get_parameters():
            parameters.append(item["id"])

        g = tokenize(BytesIO(math_expr.encode("utf-8")).readline)

        for toknum, tokval, _, _, _ in g:
            if toknum == ENCODING:
                continue

            elif toknum == NAME and tokval in parameters:
                result += "p." + str(tokval)

            elif toknum == OP and tokval in ("*", "/", "^"):
                result += "." + str(tokval)

            elif toknum == OP and tokval in ("+", "-"):
                result += " " + str(tokval) + " "

            else:
                result += str(tokval)

        return result

    def get_states(self, math_expr):
        """Return a list with the states present in the string."""
        result = []

        states = []
        for state in self.dae.get_states():
            states.append(state["id"])

        g = tokenize(BytesIO(math_expr.encode("utf-8")).readline)

        for toknum, tokval, _, _, _ in g:
            if toknum == NAME and tokval in states:
                result.append(tokval)

        return result
