const Chat = {
  async handleSend(message) {
    if (!message.trim()) return;
    
    if (State.messages.length === 0) {
      UI.hideSampleQuestions();
    }
    
    UI.renderMessage('user', message);
    State.addMessage('user', message);
    UI.clearInput();
    
    UI.showLoading();
    UI.disableInput();
    
    try {
      const history = State.getHistory().slice(0, -1);
      const response = await API.sendMessage(message, history);
      
      UI.hideLoading();
      
      UI.renderMessage('assistant', response.answer);
      State.addMessage('assistant', response.answer);
      UI.enableInput();
      
    } catch (error) {
      UI.hideLoading();
      
      if (error.type === 'RATE_LIMIT') {
        await this.handleRateLimit(message);
      } else if (error.type === 'UNAUTHORIZED' || error.type === 'SERVER_ERROR') {
        UI.showError(AppConfig.errorMessages.serverError);
        UI.enableInput();
      } else {
        UI.showError(AppConfig.errorMessages.networkError);
        UI.enableInput();
      }
    }
  },
  
  async handleSampleClick(question) {
    await this.handleSend(question);
  },
  
  async handleRateLimit(message) {
    State.isRateLimited = true;
    State.pendingMessage = message;
    
    let countdown = AppConfig.rateLimitSeconds;
    UI.showRateLimitTimer(countdown);
    
    const interval = setInterval(() => {
      countdown--;
      if (countdown > 0) {
        UI.showRateLimitTimer(countdown);
      } else {
        clearInterval(interval);
        State.isRateLimited = false;
        UI.hideRateLimitTimer();
        UI.setInputValue(State.pendingMessage);
        UI.enableInput();
        State.pendingMessage = null;
      }
    }, 1000);
  }
};