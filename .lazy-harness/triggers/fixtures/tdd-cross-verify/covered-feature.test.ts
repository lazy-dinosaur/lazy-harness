import { tddCrossVerifyCoveredFixture } from './covered-feature';

describe('tdd cross verify covered fixture', () => {
  it('has a matching test file', () => {
    expect(tddCrossVerifyCoveredFixture).toBe(1);
  });
});
