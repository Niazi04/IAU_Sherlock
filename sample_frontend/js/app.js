const App = {
  init() {
    UI.init();
    
    const hasSeenWelcome = localStorage.getItem('hasSeenWelcome') === 'true';
    if (!hasSeenWelcome) {
      UI.showModal();
    }
    
    UI.showSampleQuestions();
    this.bindEvents();
  },
  
  bindEvents() {
    UI.elements.sendButton.addEventListener('click', () => {
      Chat.handleSend(UI.elements.inputField.value);
    });
    
    UI.elements.inputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        Chat.handleSend(UI.elements.inputField.value);
      }
    });
    
    UI.elements.inputField.addEventListener('input', () => {
      UI.autoResize();
    });
    
    UI.elements.modalCloseBtn.addEventListener('click', () => {
      UI.hideModal();
      localStorage.setItem('hasSeenWelcome', 'true');
    });
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});