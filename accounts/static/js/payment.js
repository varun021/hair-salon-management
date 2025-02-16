function simulatePaymentProcessing() {
    const progressBar = document.getElementById('payment-progress');
    const statusText = document.getElementById('status-text');
    let progress = 0;

    const interval = setInterval(() => {
        progress += 10;
        progressBar.style.width = progress + '%';
        
        switch(progress) {
            case 20:
                statusText.textContent = 'Validating payment details...';
                break;
            case 50:
                statusText.textContent = 'Processing payment...';
                break;
            case 80:
                statusText.textContent = 'Finalizing transaction...';
                break;
            case 100:
                statusText.textContent = 'Payment successful!';
                clearInterval(interval);
                setTimeout(() => {
                    document.getElementById('payment-form').submit();
                }, 1000);
                break;
        }
    }, 500);
} 