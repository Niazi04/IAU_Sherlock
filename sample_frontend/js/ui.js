const UI = {
  elements: {},
  
  init() {
    this.elements = {
      chatContainer: document.getElementById('chat-messages'),
      inputField: document.getElementById('message-input'),
      sendButton: document.getElementById('send-button'),
      modal: document.getElementById('welcome-modal'),
      modalCloseBtn: document.getElementById('modal-close'),
      sampleContainer: document.getElementById('sample-questions'),
      chatWrapper: document.getElementById('chat-container')
    };
  },
  
  renderMessage(role, content) {
    const messageEl = document.createElement('div');
    messageEl.className = 'message ' + role;
    
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    
    if (role === 'user') {
      bubbleEl.textContent = content;
    } else {
      bubbleEl.innerHTML = this.formatContent(content);
    }
    
    messageEl.appendChild(bubbleEl);
    this.elements.chatContainer.appendChild(messageEl);
    this.scrollToBottom();
  },
  
  formatContent(text) {
    if (text === 'NO-ANSWER') {
      return AppConfig.noAnswerMessage;
    }
    
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    let formatted = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    
    return formatted;
  },
  
  showLoading() {
    const loadingEl = document.createElement('div');
    loadingEl.className = 'message assistant loading';
    loadingEl.id = 'loading-message';
    
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    bubbleEl.innerHTML = '<div class="loading-indicator"><div class="spinner"></div><span>در حال جستجو...</span></div>';
    
    loadingEl.appendChild(bubbleEl);
    this.elements.chatContainer.appendChild(loadingEl);
    this.scrollToBottom();
  },
  
  hideLoading() {
    const loadingEl = document.getElementById('loading-message');
    if (loadingEl) {
      loadingEl.remove();
    }
  },
  
  scrollToBottom() {
    requestAnimationFrame(() => {
      this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    });
  },
  
  disableInput() {
    this.elements.inputField.disabled = true;
    this.elements.sendButton.disabled = true;
  },
  
  enableInput() {
    this.elements.inputField.disabled = false;
    this.elements.sendButton.disabled = false;
  },
  
  showRateLimitTimer(seconds) {
    let timerEl = document.getElementById('rate-limit-timer');
    if (!timerEl) {
      timerEl = document.createElement('div');
      timerEl.id = 'rate-limit-timer';
      timerEl.className = 'rate-limit-banner';
      this.elements.chatWrapper.insertBefore(timerEl, this.elements.chatWrapper.firstChild);
    }
    
    const toPersianNum = (num) => {
      return num.toString().replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
    };
    
    timerEl.textContent = 'لطفاً ' + toPersianNum(seconds) + ' ثانیه صبر کنید...';
  },
  
  hideRateLimitTimer() {
    const timerEl = document.getElementById('rate-limit-timer');
    if (timerEl) {
      timerEl.remove();
    }
  },
  
  showError(message) {
    const errorEl = document.createElement('div');
    errorEl.className = 'message error';
    
    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';
    bubbleEl.textContent = message;
    
    errorEl.appendChild(bubbleEl);
    this.elements.chatContainer.appendChild(errorEl);
    this.scrollToBottom();
  },
  
  showSampleQuestions() {
    const samples = [
      'چند واحد باید پاس کنم تا فارق التحصیل بشم؟',
      'چرا نمیتونم کارت ورود به جلسه بگیرم؟',
      'ادرس دانشگاه تهران مرکز رو بهم بگو'
    ];
    
    this.elements.sampleContainer.innerHTML = samples
      .map(q => '<button class="sample-question">' + q + '</button>')
      .join('');
    
    this.elements.sampleContainer.querySelectorAll('.sample-question').forEach(btn => {
      btn.addEventListener('click', (e) => {
        Chat.handleSampleClick(e.target.textContent);
      });
    });
  },
  
  hideSampleQuestions() {
    this.elements.sampleContainer.style.display = 'none';
  },
  
  showModal() {
    this.elements.modal.classList.add('show');
  },
  
  hideModal() {
    this.elements.modal.classList.remove('show');
  },
  
  setInputValue(value) {
    this.elements.inputField.value = value;
    this.autoResize();
  },
  
  clearInput() {
    this.elements.inputField.value = '';
    this.autoResize();
  },
  
  autoResize() {
    const textarea = this.elements.inputField;
    textarea.style.height = 'auto';
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 44), 150);
    textarea.style.height = newHeight + 'px';
  }
};