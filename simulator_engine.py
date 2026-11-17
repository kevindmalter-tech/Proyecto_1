import re
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PySpice.Spice.Parser import SpiceParser

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class SimulationPlotWidget(QWidget):
    """Widget de PyQt5 que incrusta una gráfica de Matplotlib."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(6, 3.6), dpi=100)
        self.figure.patch.set_facecolor("#ffffff")
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.clear_plot("Esperando simulación...")

    def clear_plot(self, message="Sin datos para graficar"):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center", color="#64748b", fontsize=11)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor("#cbd5e1")
        self.canvas.draw()

    def plot_transient(self, time_vals, node_series, lab_name):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        for node_name, voltages in node_series.items():
            ax.plot(time_vals * 1000.0, voltages, linewidth=2, label=f"Nodo {node_name} (V)")
        ax.set_title(f"Respuesta Transitoria - {lab_name}", fontsize=11, fontweight="bold")
        ax.set_xlabel("Tiempo (ms)")
        ax.set_ylabel("Voltaje (V)")
        ax.grid(True, linestyle="--", alpha=0.5)
        if node_series:
            ax.legend(loc="best", fontsize=9)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_dc_bars(self, node_voltages, branch_currents, lab_name):
        self.figure.clear()
        has_currents = len(branch_currents) > 0
        ax1 = self.figure.add_subplot(1, 2 if has_currents else 1, 1)

        nodes = list(node_voltages.keys())
        volts = list(node_voltages.values())
        bars = ax1.bar(nodes, volts, color="#2563eb", width=0.5)
        ax1.set_title(f"Voltajes de Nodos - {lab_name}", fontsize=10, fontweight="bold")
        ax1.set_ylabel("Voltaje (V)")
        ax1.grid(True, axis="y", linestyle="--", alpha=0.5)
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2.0, yval, f"{yval:.2f}V",
                     ha="center", va="bottom", fontsize=8, fontweight="bold")

        if has_currents:
            ax2 = self.figure.add_subplot(1, 2, 2)
            branches = list(branch_currents.keys())
            currs_ma = [c * 1000.0 for c in branch_currents.values()]
            bars2 = ax2.bar(branches, currs_ma, color="#16a34a", width=0.5)
            ax2.set_title("Corrientes de Fuentes/Mallas", fontsize=10, fontweight="bold")
            ax2.set_ylabel("Corriente (mA)")
            ax2.grid(True, axis="y", linestyle="--", alpha=0.5)
            for bar in bars2:
                yval = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2.0, yval, f"{yval:.2f}mA",
                         ha="center", va="bottom", fontsize=8, fontweight="bold")

        self.figure.tight_layout()
        self.canvas.draw()


def detect_circuit_type(cir_text):
    """Identifica el tipo de laboratorio según los componentes del archivo .cir."""
    lines = [
        line.strip().upper()
        for line in cir_text.splitlines()
        if line.strip() and not line.strip().startswith(("*", ";", "."))
    ]
    has_c = any(l.startswith("C") for l in lines)
    has_l = any(l.startswith("L") for l in lines)
    resistors = [l for l in lines if l.startswith("R")]
    sources = [l for l in lines if l.startswith(("V", "I"))]

    if has_c and has_l:
        return "Circuito RLC (Análisis Transitorio)"
    if has_c:
        return "Circuito RC (Análisis Transitorio)"
    if has_l:
        return "Circuito RL (Análisis Transitorio)"
    if len(resistors) == 2 and len(sources) == 1:
        return "Divisor de Voltaje (Análisis DC)"
    if len(sources) > 1 or len(resistors) >= 3:
        return "Análisis de Mallas / Nodos (DC)"
    return "Circuito DC General"


def _parse_tran_directive(cir_text):
    """Extrae step_time y end_time si el .cir incluye una directiva .TRAN."""
    for line in cir_text.splitlines():
        clean = line.strip().lower()
        if clean.startswith(".tran"):
            parts = clean.split()
            if len(parts) >= 3:
                try:
                    step = _spice_unit_to_float(parts[1])
                    end = _spice_unit_to_float(parts[2])
                    if step > 0 and end > step:
                        return step, end
                except ValueError:
                    pass
    return 1e-4, 1e-2


def _spice_unit_to_float(token):
    units = {
        "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6,
        "m": 1e-3, "k": 1e3, "meg": 1e6, "g": 1e9
    }
    match = re.match(r"^([+-]?\d*\.?\d+(?:e[+-]?\d+)?)([a-z]*)$", token.strip().lower())
    if not match:
        raise ValueError(f"Valor inválido: {token}")
    val = float(match.group(1))
    suffix = match.group(2).rstrip("s")
    return val * units.get(suffix, 1.0)


def run_circuit_simulation(cir_text, lab_name):
    """
    Ejecuta la simulación con PySpice y devuelve un diccionario estructurado:
    {
        "circuit_type": str,
        "mode": "transient" | "dc",
        "report": str,
        "time": ndarray (si transient),
        "node_series": dict (si transient),
        "node_voltages": dict (si dc),
        "branch_currents": dict (si dc)
    }
    """
    circuit_type = detect_circuit_type(cir_text)
    try:
        parser = SpiceParser(source=cir_text)
        circuit = parser.build_circuit()
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)

        has_reactive = any(
            line.strip().upper().startswith(("C", "L"))
            for line in cir_text.splitlines()
        )

        lines_out = [
            f"====================================================",
            f" LABORATORIO: {lab_name}",
            f" TIPO DETECTADO: {circuit_type}",
            f"====================================================\n"
        ]

        if has_reactive:
            step_time, end_time = _parse_tran_directive(cir_text)
            analysis = simulator.transient(step_time=step_time, end_time=end_time)
            time_arr = analysis.time.as_ndarray()
            node_series = {}

            lines_out.append(f"Modo: Análisis Transitorio (paso={step_time}s, fin={end_time}s)\n")
            header = f"{'Tiempo (ms)':>12} | " + " | ".join(f"V({n}) [V]" for n in analysis.nodes)
            lines_out.append(header)
            lines_out.append("-" * len(header))

            for name in analysis.nodes:
                node_series[str(name)] = analysis[name].as_ndarray()

            step_idx = max(len(time_arr) // 12, 1)
            for i in range(0, len(time_arr), step_idx):
                row = f"{time_arr[i]*1000:>12.4f} | " + " | ".join(
                    f"{node_series[str(n)][i]:>9.4f}" for n in analysis.nodes
                )
                lines_out.append(row)

            return {
                "circuit_type": circuit_type,
                "mode": "transient",
                "report": "\n".join(lines_out),
                "time": time_arr,
                "node_series": node_series,
            }
        else:
            analysis = simulator.operating_point()
            node_voltages = {}
            branch_currents = {}

            lines_out.append("Modo: Punto de Operación DC (Nodos y Mallas)\n")
            lines_out.append("--- VOLTAJES EN NODOS ---")
            for name, node in analysis.nodes.items():
                val = float(node[0])
                node_voltages[str(name)] = val
                lines_out.append(f"  • Nodo [{name}]: {val:.4f} V")

            if analysis.branches:
                lines_out.append("\n--- CORRIENTES EN RAMAS / MALLAS ---")
                for name, branch in analysis.branches.items():
                    curr = float(branch[0])
                    branch_currents[str(name)] = curr
                    lines_out.append(f"  • Rama [{name}]: {curr:.6f} A  ({curr*1000:.3f} mA)")

            return {
                "circuit_type": circuit_type,
                "mode": "dc",
                "report": "\n".join(lines_out),
                "node_voltages": node_voltages,
                "branch_currents": branch_currents,
            }

    except Exception as exc:
        raise RuntimeError(f"Error al simular el circuito:\n{exc}") from exc