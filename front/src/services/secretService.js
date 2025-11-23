import axios from 'axios';
import { authService } from './authService';
const API_URL = process.env.VUE_APP_API_URL || 'http://localhost:8888';

function getAuthHeaders() {
  const token = authService.getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const secretService = {
  async listSecrets() {
    const response = await axios.get(`${API_URL}/secrets`, { headers: getAuthHeaders() });
    return response.data;
  },
  async createSecret({ name, service_type, datos_secrets }) {
    const response = await axios.post(
      `${API_URL}/secrets`,
      { name, service_type, datos_secrets },
      { headers: getAuthHeaders() }
    );
    return response.data;
  },
  async updateSecret(secret_id, data) {
    const response = await axios.put(
      `${API_URL}/secrets/${secret_id}`,
      data,
      { headers: getAuthHeaders() }
    );
    return response.data;
  },
  async deleteSecret(secret_id) {
    await axios.delete(`${API_URL}/secrets/${secret_id}`, {
      headers: getAuthHeaders(),
    });
    return true;
  },
  async getDecryptableSecrets() {
    console.log("ACA", getAuthHeaders())
    const response = await axios.get(`${API_URL}/secrets/get-decryptable`, { headers: getAuthHeaders() });
    console.log(response.data)
    return response.data;
  },
};
