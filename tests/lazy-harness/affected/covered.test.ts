import { describe, expect, it } from 'bun:test';
import { affectedCoveredValue } from './covered';

describe('affectedCoveredValue', () => {
  it('increments by one', () => {
    expect(affectedCoveredValue(1)).toBe(2);
  });
});
