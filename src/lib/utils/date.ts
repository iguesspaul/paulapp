export function getYearProgress() {
    const now = new Date();
    const start = new Date(now.getFullYear(), 0, 0);
    const diff = now.getTime() - start.getTime();
    const oneDay = 1000 * 60 * 60 * 24;
    const dayOfYear = Math.floor(diff / oneDay);
    
    const percentage = Math.floor((dayOfYear / 365) * 100);
    const tens = Math.max(1, Math.floor(percentage / 10));
    const bar = "X".repeat(tens) + "0".repeat(10 - tens);
    
    return { dayOfYear, percentage, bar };
}

export function getCountdownDisplay(targetTimestamp: number) {
    const target = new Date(targetTimestamp * 1000);
    const now = new Date();
    const diffTime = target.getTime() - now.getTime();
    const daysRemaining = Math.max(0, Math.ceil(diffTime / (1000 * 60 * 60 * 24)));
    const isToday = target.getDate() === now.getDate() && target.getMonth() === now.getMonth() && target.getFullYear() === now.getFullYear();
    
    return { daysRemaining, isToday };
}
