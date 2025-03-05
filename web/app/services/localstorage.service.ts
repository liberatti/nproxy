import { Injectable } from '@angular/core';
import { delay } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class LocalStorageService {
  private storage: Storage;
  constructor() {
    this.storage = window.localStorage;
  }
  exists(key: string): boolean {
    return key in this.storage;
  }
  wait(key: string, timeout: number) {
    let i = timeout / 1000;
    while (i > 0) {
      if (this.storage[key]) {
        break;
      }
      delay(1000);
      i--;
    }
  }
  set(key: string, value: any): boolean {
    if (this.storage) {
      this.storage[key] = JSON.stringify(value);
      return true;
    }
    return false;
  }
  get(key: string): any {
    if (this.storage) {
      try {
        return JSON.parse(this.storage[key]);
      } catch (e) {

      }

    }
    return null;
  }

  remove(key: string): boolean {
    if (this.storage) {
      this.storage.removeItem(key);
      return true;
    }
    return false;
  }

  clear(): boolean {
    if (this.storage) {
      this.storage.clear();
      return true;
    }
    return false;
  }
}
