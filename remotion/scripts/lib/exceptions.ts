/**
 * exceptions.ts
 * ─────────────
 * Schema and validation for known-exceptions.json waivers.
 *
 * Each waiver must be an array item:
 * {
 *   rule: string,
 *   reason: string,
 *   approvedBy: string,
 *   expires: string (YYYY-MM-DD)
 * }
 */

export interface Waiver {
  rule: string;
  reason: string;
  approvedBy: string;
  expires: string;
}

export function validateWaivers(raw: unknown): {valid: boolean; waivers: Waiver[]; errors: string[]} {
  const errors: string[] = [];
  const waivers: Waiver[] = [];

  if (!Array.isArray(raw)) {
    return {
      valid: false,
      waivers: [],
      errors: ['known-exceptions.json must be an array of waiver objects {rule, reason, approvedBy, expires}']
    };
  }

  const today = new Date().toISOString().slice(0, 10);

  for (let i = 0; i < raw.length; i++) {
    const item = raw[i];
    if (typeof item !== 'object' || item === null) {
      errors.push(`Waiver at index ${i} is not an object`);
      continue;
    }
    const {rule, reason, approvedBy, expires} = item as Record<string, unknown>;
    if (!rule || typeof rule !== 'string') {
      errors.push(`Waiver at index ${i} missing required string field 'rule'`);
    }
    if (!reason || typeof reason !== 'string') {
      errors.push(`Waiver at index ${i} missing required string field 'reason'`);
    }
    if (!approvedBy || typeof approvedBy !== 'string') {
      errors.push(`Waiver at index ${i} missing required string field 'approvedBy'`);
    }
    if (!expires || typeof expires !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(expires)) {
      errors.push(`Waiver at index ${i} missing or invalid 'expires' format (expected YYYY-MM-DD)`);
    } else if (expires < today) {
      errors.push(`Waiver for rule '${rule}' expired on ${expires}`);
    }

    if (errors.length === 0) {
      waivers.push({
        rule: String(rule),
        reason: String(reason),
        approvedBy: String(approvedBy),
        expires: String(expires)
      });
    }
  }

  return {
    valid: errors.length === 0,
    waivers,
    errors
  };
}
