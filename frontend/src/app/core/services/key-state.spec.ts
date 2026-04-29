import { TestBed } from '@angular/core/testing';

import { KeyState } from './key-state';

describe('KeyState', () => {
  let service: KeyState;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(KeyState);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
