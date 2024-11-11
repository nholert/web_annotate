/* Calendar */
const options = {
    showHeader: false,
    showClearButton: false,
    showTodayButton: false,
    isRange: true,
    enableMonthSwitch: false,
    enableYearSwitch: false,
    displayMode: "inline",
    type: 'date',
    surveyDate: new Date(survey_date) // The date you want all calendars to start from
};

// Attach and configure each calendar instance
const calendars = bulmaCalendar.attach('[type="date"]', options);

// Set all calendars to display starting from surveyDate
calendars.forEach((calendar, index) => {
    // Set the initial display month for each calendar to surveyDate
    calendar.options.date = new Date(survey_date);
    calendar.value(new Date(survey_date)); // Set the value to force the initial display

    // Adjust subsequent calendars to display consecutive months
    if (index > 0) {
        let newMonthDate = new Date(survey_date);
        newMonthDate.setMonth(newMonthDate.getMonth() + index); // Increment month for each subsequent calendar
        calendar.value(newMonthDate); // Set the display to the consecutive month
    }

    // Ensure unique highlighting with startDate and endDate
    calendar.options.startDate = new Date(early_date); // Replace with tab-specific early_date
    calendar.options.endDate = new Date(late_date); // Replace with tab-specific late_date
    calendar.refresh(); // Refresh the calendar to apply changes
});

// Ensure calendars are displayed on page load
window.addEventListener('DOMContentLoaded', () => {
    calendars.forEach(calendar => {
        calendar.show(); // Ensure calendars render on page load
    });
});
