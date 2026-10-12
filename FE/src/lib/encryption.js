import CryptoJS from 'crypto-js';
import JSEncrypt from 'jsencrypt';
import { storage } from './storage';

/** AES-256-CBC key length in bits */
const AES_KEY_SIZE = 256;

/**
 * Generates a random AES key.
 * @returns {CryptoJS.lib.WordArray}
 */
function generateAesKey() {
  return CryptoJS.lib.WordArray.random(AES_KEY_SIZE / 8);
}

/**
 * Generates a random IV.
 * @returns {CryptoJS.lib.WordArray}
 */
function generateIv() {
  return CryptoJS.lib.WordArray.random(16);
}

/**
 * Encrypts a payload using AES-256-CBC, then wraps the AES key with RSA.
 * @param {object} payload - Plain object to encrypt
 * @param {string} publicKeyPem - RSA public key in PEM format
 * @returns {{ encryptedData: string, encryptedKey: string, iv: string }}
 * @throws {Error} If publicKeyPem is not provided
 */
export function encryptPayload(payload, publicKeyPem) {
  if (!publicKeyPem) {
    throw new Error('RSA public key is required for encryption');
  }

  const aesKey = generateAesKey();
  const iv = generateIv();
  const payloadStr = JSON.stringify(payload);

  // AES-256-CBC encrypt the payload
  const encrypted = CryptoJS.AES.encrypt(payloadStr, aesKey, {
    iv,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });

  // RSA-wrap the AES key
  const encryptor = new JSEncrypt();
  encryptor.setPublicKey(publicKeyPem);
  const encryptedKey = encryptor.encrypt(aesKey.toString(CryptoJS.enc.Base64));

  if (!encryptedKey) {
    throw new Error('RSA encryption of AES key failed');
  }

  return {
    encryptedData: encrypted.ciphertext.toString(CryptoJS.enc.Base64),
    encryptedKey,
    iv: iv.toString(CryptoJS.enc.Base64),
  };
}

/** @type {string | null} */
let _cachedPublicKey = null;

/**
 * Returns the cached RSA public key from env or storage.
 * @returns {string | null}
 */
export function getPublicKey() {
  if (_cachedPublicKey) return _cachedPublicKey;

  _cachedPublicKey =
    import.meta.env.VITE_RSA_PUBLIC_KEY || storage.get('rsaPublicKey') || null;

  return _cachedPublicKey;
}
