clc
clear

ADD_WIN_FLAG = 1;
LOG_PLOT_FLAG = 1;
DC_REMOVE_FLAG = 1;

name = "MASH 4bit input 255";
figname = "results/dither_mash_4bit_255_psd.svg";
figname_time = "results/dither-mash4bit.svg";
x = load("../HK-MASH-DDSM/dither-mash111-hkefm-data-4bit-a2-reg-new.txt");

x = double(x);

avg_val = mean(x);
fprintf("Average output value: %.6f\n", avg_val);

figure;
plot(x);
grid on;
title('Time Domain Output');
xlabel('Sample');
ylabel('Value');
saveas(gcf, figname_time);

L = length(x);
N = 2^(nextpow2(L)-1);
x = x(1:N);

if DC_REMOVE_FLAG
    average = mean(x);
    x = x - average;
end

if ADD_WIN_FLAG
    wn = hann(N);
    x = x .* wn;
end

xdft = fft(x, N);
psdx = xdft .* conj(xdft) / N;

if ADD_WIN_FLAG
    zz = wn .* wn;
    zz1 = sum(zz);
    psdx = psdx * N / zz1;
end

spsdx = psdx(1:floor(N/2)+1) * 2;
spsdx(1) = psdx(1);

spsdx_log = 10 * log10(spsdx);
spsdx_log(spsdx_log == -inf) = -300;

freq = 0:(2*pi)/N:pi;
NTF = 3*20*log10(2*sin(freq/2));

figure;
if LOG_PLOT_FLAG
    semilogx(freq/pi, spsdx_log, freq/pi, NTF, '--')
else
    plot(freq/pi, spsdx_log, freq/pi, NTF, '--')
end
grid on
legend(name, 'NTF','Location', 'northwest')
title('Periodogram Using FFT')
xlabel('Normalized Frequency (\times\pi rad/sample)')
ylabel('Power/Frequency (dB/rad/sample)')
saveas(gcf, figname)