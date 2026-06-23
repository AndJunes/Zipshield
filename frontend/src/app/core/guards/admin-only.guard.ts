import { roleGuard } from './role.guard';

export const adminOnlyGuard = roleGuard(['admin']);
export const adminOrSupervisorGuard = roleGuard(['admin', 'supervisor']);
