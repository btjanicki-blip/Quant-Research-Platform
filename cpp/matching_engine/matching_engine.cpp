#include <algorithm>
#include <pybind11/pybind11.h>
#include <stdexcept>

namespace py = pybind11;

// A narrow, testable extension point for hot-path matching logic.  Python owns orchestration.
double executable_quantity(double requested, double bar_volume, double participation) {
    if (requested < 0.0 || bar_volume < 0.0 || participation < 0.0 || participation > 1.0) {
        throw std::invalid_argument("invalid matching inputs");
    }
    return std::min(requested, bar_volume * participation);
}

PYBIND11_MODULE(quant_matching_engine, module) {
    module.doc() = "Performance-critical matching primitives";
    module.def("executable_quantity", &executable_quantity);
}
