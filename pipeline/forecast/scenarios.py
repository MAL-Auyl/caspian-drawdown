"""Три сценария прогноза расстояния до воды: линейная экстраполяция с
разными допущениями плюс полиномиальное ускорение для пессимистичного."""

HORIZONS = (2030, 2035, 2040)


def build_scenarios(current_distance_m: float, speed_m_per_year: float, last_year: int, horizons=HORIZONS) -> dict:
    def scenario(mult: float, poly: bool = False) -> dict:
        out = {}
        for h in horizons:
            dy = h - last_year
            delta = speed_m_per_year * dy * mult
            if poly:
                delta *= 1 + 0.015 * dy
            out[str(h)] = round(max(current_distance_m - delta, 0), 0)
        return out

    return {
        "optimistic": scenario(0.75),
        "baseline": scenario(1.0),
        "pessimistic": scenario(1.25, poly=True),
    }
