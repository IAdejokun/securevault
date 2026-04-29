import { TestBed } from '@angular/core/testing';

import { ApiKey } from './api-key';

describe('ApiKey', () => {
  let service: ApiKey;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ApiKey);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
