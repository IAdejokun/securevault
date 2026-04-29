import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class KeyStateService {
  private _pendingRawKey: string | null = null;
  private _pendingKeyName: string | null = null;

  setPendingRotation(rawKey: string, keyName: string) {
    this._pendingRawKey = rawKey;
    this._pendingKeyName = keyName;
  }

  consumePendingRotation(): { rawKey: string; keyName: string } | null {
    if (!this._pendingRawKey) return null;
    const result = {
      rawKey: this._pendingRawKey,
      keyName: this._pendingKeyName ?? '',
    };
    this._pendingRawKey = null;
    this._pendingKeyName = null;
    return result;
  }
}
