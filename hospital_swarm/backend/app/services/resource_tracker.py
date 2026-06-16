from typing import Dict, Any, List

RESOURCE_LIMITS = {
    "icu_beds": {"total": 5, "used": 0, "label": "ICU Beds"},
    "pharmacy_stock": {"total": 20, "used": 0, "label": "Pharmacy Stock"},
    "ambulance_available": {"total": 3, "used": 0, "label": "Ambulances"},
}


class ResourceTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.resources = {k: dict(v) for k, v in RESOURCE_LIMITS.items()}
        return cls._instance

    def get_status(self) -> Dict[str, Any]:
        return {
            name: {
                "total": info["total"],
                "used": info["used"],
                "available": info["total"] - info["used"],
                "label": info["label"],
            }
            for name, info in self.resources.items()
        }

    def use_resource(self, name: str) -> bool:
        if name not in self.resources:
            return False
        res = self.resources[name]
        if res["used"] < res["total"]:
            res["used"] += 1
            return True
        return False

    def release_resource(self, name: str):
        if name in self.resources:
            self.resources[name]["used"] = max(0, self.resources[name]["used"] - 1)

    def check_shortages(self) -> List[str]:
        return [name for name, info in self.resources.items() if info["used"] >= info["total"]]

    def reset(self):
        for name, info in RESOURCE_LIMITS.items():
            if name in self.resources:
                self.resources[name]["used"] = info["used"]
