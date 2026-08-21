/**
 * Configuration File
 * Edit these values to match your backend setup.
 */
const AppConfig = {
  // IMPORTANT: Change 8000 to your actual backend port. 
  // Use 127.0.0.1 or localhost, NOT 0.0.0.0 (which is for server binding only)
  apiUrl: 'http://127.0.0.1:8000/sherlock/chat', 
  
  apiKey: 'VerySecure!API!key',
  
  noAnswerMessage: 'متاسفم، پاسخی برای این سوال پیدا نکردم.',
  
  rateLimitSeconds: 20,
  
  errorMessages: {
    serverError: 'سرور در حال حاضر در دسترس نیست. لطفاً بعداً تلاش کنید.',
    networkError: 'خطا در ارتباط با سرور. لطفاً اتصال اینترنت خود را بررسی کنید.'
  }
};