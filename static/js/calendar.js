class Calendar {
    constructor(containerElement) {
        this.container = containerElement;
        this.currentDate = new Date();
        this.displayedDate = new Date();
        this.events = [];
        this.timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        this.setupFileImport();
    }

    async init() {
        await this.fetchEvents();
        this.render();
    }

    async fetchEvents() {
        const response = await fetch(`/get_class_meetings?timezone=${encodeURIComponent(this.timeZone)}`);
        this.events = await response.json();
    }

    setupFileImport() {
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.csv,.txt';
        fileInput.style.display = 'none';
        this.container.parentNode.appendChild(fileInput);

        const importButton = document.createElement('button');
        importButton.textContent = 'Import Schedule';
        importButton.onclick = () => fileInput.click();
        this.container.parentNode.insertBefore(importButton, this.container);

        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/import_file', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    alert(data.message);
                    await this.fetchEvents();
                    this.render();
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred while importing the file.');
                }
            }
        });
    }

    render() {
        const year = this.displayedDate.getFullYear();
        const month = this.displayedDate.getMonth();
        this.container.innerHTML = `
            <div class="calendar-header">
                <button onclick="calendar.prevMonth()">&lt;</button>
                <h2>${new Date(year, month).toLocaleString('default', { month: 'long', year: 'numeric' })}</h2>
                <button onclick="calendar.nextMonth()">&gt;</button>
                <button onclick="calendar.goToToday()">Today</button>
            </div>
            <div class="calendar-grid">
                ${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => `<div class="calendar-day">${day}</div>`).join('')}
                ${this.getDaysInMonth(year, month).map(date => this.renderDay(date)).join('')}
            </div>
        `;
    }

    renderDay(date) {
        const isOtherMonth = date.getMonth() !== this.displayedDate.getMonth();
        const isToday = this.isToday(date);
        const dayEvents = this.events.filter(event => {
            const eventDate = new Date(event.start);
            return eventDate.getDate() === date.getDate() &&
                   eventDate.getMonth() === date.getMonth() &&
                   eventDate.getFullYear() === date.getFullYear();
        });
    
        return `
            <div class="calendar-day ${isOtherMonth ? 'other-month' : ''} ${isToday ? 'today' : ''}">
                ${date.getDate()}
                ${dayEvents.map(event => {
                    const startTime = new Date(event.start);
                    const endTime = new Date(event.end);
                    const timeFormat = { hour: 'numeric', minute: '2-digit', hour12: true };
                    return `
                        <div class="event" onclick="calendar.showEventDetails('${event.title}', '${event.start}', '${event.end}')">
                            ${event.title}<br>
                            ${startTime.toLocaleTimeString(undefined, timeFormat)} - 
                            ${endTime.toLocaleTimeString(undefined, timeFormat)}
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    getDaysInMonth(year, month) {
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const days = [];

        for (let i = 1 - firstDay.getDay(); i <= lastDay.getDate(); i++) {
            days.push(new Date(year, month, i));
        }

        return days;
    }

    prevMonth() {
        this.displayedDate.setMonth(this.displayedDate.getMonth() - 1);
        this.render();
    }

    nextMonth() {
        this.displayedDate.setMonth(this.displayedDate.getMonth() + 1);
        this.render();
    }

    goToToday() {
        this.displayedDate = new Date();
        this.render();
    }

    isToday(date) {
        const today = new Date();
        return date.getDate() === today.getDate() &&
               date.getMonth() === today.getMonth() &&
               date.getFullYear() === today.getFullYear();
    }

    showEventDetails(title, start, end) {
        const startDate = new Date(start);
        const endDate = new Date(end);
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            hour: 'numeric', 
            minute: 'numeric',
            timeZone: this.timeZone
        };
        const formattedStart = startDate.toLocaleString(undefined, options);
        const formattedEnd = endDate.toLocaleString(undefined, options);
        alert(`Event: ${title}\nStart: ${formattedStart}\nEnd: ${formattedEnd}\nTime Zone: ${this.timeZone}`);
    }
}