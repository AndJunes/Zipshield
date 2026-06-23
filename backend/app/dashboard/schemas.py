from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_supervisors: int
    total_agents: int
    total_clients: int
    active_clients: int
    inactive_clients: int
    total_policies: int
    active_policies: int
    expired_policies: int
    debtor_clients: int
    active_policies_value: float