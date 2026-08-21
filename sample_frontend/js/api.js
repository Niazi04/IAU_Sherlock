const API = {
  async sendMessage(query, history = []) {
    try {
      const response = await fetch(AppConfig.apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': AppConfig.apiKey
        },
        body: JSON.stringify({
          query: query,
          history: history
        })
      });
      
      if (response.status === 429) throw { type: 'RATE_LIMIT', status: 429 };
      if (response.status === 401) throw { type: 'UNAUTHORIZED', status: 401 };
      if (response.status >= 500) throw { type: 'SERVER_ERROR', status: response.status };
      if (!response.ok) throw { type: 'UNKNOWN_ERROR', status: response.status };
      
      return await response.json();
    } catch (error) {
      if (error.type) throw error;
      throw { type: 'NETWORK_ERROR', status: 0 };
    }
  }
};