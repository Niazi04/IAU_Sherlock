const State = {
  messages: [],
  isLoading: false,
  isRateLimited: false,
  rateLimitCountdown: 0,
  pendingMessage: null,
  
  addMessage(role, content) {
    this.messages.push({ role, content });
  },
  
  getLastMessage() {
    return this.messages[this.messages.length - 1];
  },
  
  getHistory() {
    return this.messages.map(msg => ({
      role: msg.role,
      content: msg.content
    }));
  },
  
  reset() {
    this.messages = [];
    this.isLoading = false;
    this.isRateLimited = false;
    this.rateLimitCountdown = 0;
    this.pendingMessage = null;
  }
};