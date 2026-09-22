(function () {
    const lengthSelect = document.getElementById('length-select');
    const seedInput = document.getElementById('seed-input');
    const tapsContainer = document.getElementById('taps-container');
    const registerView = document.getElementById('register-view');
    const outputStream = document.getElementById('output-stream');
    const stepCountEl = document.getElementById('step-count');
    const outputBitEl = document.getElementById('output-bit');
    const feedbackBitEl = document.getElementById('feedback-bit');
    const stepBtn = document.getElementById('step-btn');
    const runBtn = document.getElementById('run-btn');
    const resetBtn = document.getElementById('reset-btn');
    const speedRange = document.getElementById('speed-range');

    // Known maximal-length tap sets (bit positions, 1-indexed from the left/MSB).
    const DEFAULT_TAPS = {
        4: [4, 3],
        8: [8, 6, 5, 4],
        16: [16, 15, 13, 4],
        32: [32, 22, 2, 1],
    };

    const MAX_OUTPUT_CHARS = 512;

    let register = [];
    let length = 8;
    let stepCount = 0;
    let outputBits = '';
    let runTimer = null;

    function defaultSeed(n) {
        return '0'.repeat(n - 1) + '1';
    }

    function buildTaps(n, selected) {
        tapsContainer.innerHTML = '';
        for (let pos = 1; pos <= n; pos++) {
            const chip = document.createElement('label');
            chip.className = 'tap-chip';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = String(pos);
            checkbox.checked = selected.includes(pos);
            checkbox.addEventListener('change', renderRegister);

            const text = document.createElement('span');
            text.textContent = pos;

            chip.appendChild(checkbox);
            chip.appendChild(text);
            tapsContainer.appendChild(chip);
        }
    }

    function getTaps() {
        return Array.from(tapsContainer.querySelectorAll('input:checked')).map((el) => Number(el.value));
    }

    function setup(n) {
        length = n;
        buildTaps(n, DEFAULT_TAPS[n] || [n, 1]);
        seedInput.value = defaultSeed(n);
        seedInput.maxLength = n;
        loadSeed();
    }

    function loadSeed() {
        let seed = seedInput.value.trim();
        if (!/^[01]+$/.test(seed) || seed.length !== length) {
            seed = defaultSeed(length);
            seedInput.value = seed;
        }
        if (/^0+$/.test(seed)) {
            seed = seed.slice(0, -1) + '1';
            seedInput.value = seed;
        }
        register = seed.split('').map(Number);
        stepCount = 0;
        outputBits = '';
        outputBitEl.textContent = '-';
        feedbackBitEl.textContent = '-';
        renderRegister();
        renderStats();
    }

    function renderRegister(pulseIndex) {
        const taps = getTaps();
        registerView.innerHTML = '';
        register.forEach((bit, i) => {
            const box = document.createElement('div');
            box.className = 'bit-box' + (bit ? ' one' : '') + (taps.includes(i + 1) ? ' tapped' : '') + (pulseIndex === i ? ' pulse' : '');
            box.textContent = bit;
            registerView.appendChild(box);
        });
    }

    function renderStats() {
        stepCountEl.textContent = stepCount;
        outputStream.textContent = outputBits.length > MAX_OUTPUT_CHARS
            ? '...' + outputBits.slice(-MAX_OUTPUT_CHARS)
            : outputBits;
    }

    function step() {
        const taps = getTaps();
        if (taps.length === 0) {
            stop();
            return;
        }
        const feedback = taps.reduce((acc, pos) => acc ^ register[pos - 1], 0);
        const output = register[register.length - 1];

        register = [feedback, ...register.slice(0, -1)];
        stepCount++;
        outputBits += output;

        outputBitEl.textContent = output;
        feedbackBitEl.textContent = feedback;
        renderRegister(0);
        renderStats();
    }

    function start() {
        if (runTimer) return;
        runBtn.classList.add('running');
        runBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop';
        runTimer = setInterval(step, Number(speedRange.value));
    }

    function stop() {
        clearInterval(runTimer);
        runTimer = null;
        runBtn.classList.remove('running');
        runBtn.innerHTML = '<i class="fa-solid fa-play"></i> Run';
    }

    lengthSelect.addEventListener('change', () => {
        stop();
        setup(Number(lengthSelect.value));
    });

    seedInput.addEventListener('change', () => {
        stop();
        loadSeed();
    });

    stepBtn.addEventListener('click', () => {
        stop();
        step();
    });

    runBtn.addEventListener('click', () => {
        if (runTimer) {
            stop();
        } else {
            start();
        }
    });

    resetBtn.addEventListener('click', () => {
        stop();
        loadSeed();
    });

    speedRange.addEventListener('change', () => {
        if (runTimer) {
            stop();
            start();
        }
    });

    setup(length);
})();
