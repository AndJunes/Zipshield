import { UserRole } from '../models';
import { MOCK_SUPERVISORS_BASE } from '../../features/supervisors/mock-supervisors';
import { MOCK_AGENTS_BASE } from '../../features/agents/mock-agents';

export interface MockUser {
  email: string;
  passwordHash: string;
  salt: string;
  role: UserRole;
  refId: number | null;
  firstName: string;
  lastName: string;
  photoUrl: string;
}

const slug = (s: string) =>
  s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

const emailFor = (firstName: string, lastName: string) =>
  `${slug(firstName)}.${slug(lastName.replace(/\s+/g, ''))}@zipshield.io`;

/**
 * SOLO PARA DESARROLLO. En producción backend mantiene los hashes y nunca
 * existe un mapa plaintext en frontend. Aquí solo lo usamos para precomputar
 * los hashes al cargar el módulo y para los chips de quick-login.
 */
export const DEMO_PASSWORDS: Record<string, string> = {};

type MockUserSeed = Omit<MockUser, 'passwordHash'>;

function buildSeeds(): { seed: MockUserSeed; plaintext: string }[] {
  const seeds: { seed: MockUserSeed; plaintext: string }[] = [];

  seeds.push({
    seed: {
      email: 'admin@zipshield.io',
      salt: 'admin-salt-2026',
      role: 'admin',
      refId: null,
      firstName: 'Admin',
      lastName: 'Zipshield',
      photoUrl: 'https://i.pravatar.cc/300?u=admin-zipshield',
    },
    plaintext: 'admin1234',
  });

  for (const sup of MOCK_SUPERVISORS_BASE) {
    const [firstName, ...rest] = sup.fullName.split(' ');
    const lastName = rest.join(' ');
    seeds.push({
      seed: {
        email: emailFor(firstName, lastName),
        salt: `supervisor-salt-${sup.id}`,
        role: 'supervisor',
        refId: sup.id,
        firstName,
        lastName,
        photoUrl: sup.photoUrl,
      },
      plaintext: 'super1234',
    });
  }

  for (const agent of MOCK_AGENTS_BASE) {
    const [firstName, ...rest] = agent.fullName.split(' ');
    const lastName = rest.join(' ');
    seeds.push({
      seed: {
        email: emailFor(firstName, lastName),
        salt: `agent-salt-${agent.id}`,
        role: 'agent',
        refId: agent.id,
        firstName,
        lastName,
        photoUrl: agent.photoUrl,
      },
      plaintext: 'agent1234',
    });
  }

  return seeds;
}

export async function hashPassword(
  plaintext: string,
  salt: string,
): Promise<string> {
  const data = new TextEncoder().encode(salt + plaintext);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(hashBuffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

export async function verifyPassword(
  plaintext: string,
  expectedHash: string,
  salt: string,
): Promise<boolean> {
  return (await hashPassword(plaintext, salt)) === expectedHash;
}

const SEEDS = buildSeeds();
SEEDS.forEach(({ seed, plaintext }) => {
  DEMO_PASSWORDS[seed.email] = plaintext;
});

export const MOCK_USERS: MockUser[] = SEEDS.map(({ seed }) => ({
  ...seed,
  passwordHash: '',
}));

export const MOCK_USERS_READY: Promise<void> = (async () => {
  await Promise.all(
    SEEDS.map(async ({ seed, plaintext }, idx) => {
      MOCK_USERS[idx].passwordHash = await hashPassword(plaintext, seed.salt);
    }),
  );
})();

export async function findMockUserByEmail(
  email: string,
): Promise<MockUser | undefined> {
  await MOCK_USERS_READY;
  return MOCK_USERS.find((u) => u.email.toLowerCase() === email.toLowerCase());
}
