const validate = (value) => {
    return value !== "" && 0 <= value && value <= 50;
};

const round = (value) => {
    if (value < 0) {
        return 0;
    } else if (value > 50) {
        return 50;
    } else {
        return value;
    }
};

const convex_combination = (self, target) => {
    target.val(50 - self.val(round(self.val())).val());
};

const convex_handle = (self) => {
    self = $(self);
    target = $(`#${self.attr('target')}`);
    convex_combination(self, target);
    let self_id = self.attr('id');
    let target_id = target.attr('id');
    let self_rate = Number(self_id.split('-')[1]) / 100;
    let target_rate = Number(target_id.split('-')[1]) / 100;

    $(`#${self_id}-result`).text(`\$${(self_rate * self.val()).toFixed(2)}`);
    $(`#${target_id}-result`).text(`\$${(target_rate * target.val()).toFixed(2)}`);
};

/* Calendar Initialization */
const options = {
    showHeader: false,
    showClearButton: false,
    showTodayButton: false,
    isRange: true,
    enableMonthSwitch: false,
    enableYearSwitch: false,
    displayMode: "inline",
    type: 'date',
    surveyDate: new Date(survey_date) // The date to start all calendars from
};

// Attach and configure each calendar instance
const calendars = bulmaCalendar.attach('[type="date"]', options);

// Set all calendars to start at surveyDate and display consecutive months
calendars.forEach((calendar, index) => {
    // Set the initial display month to surveyDate
    calendar.options.date = new Date(survey_date);
    calendar.value(new Date(survey_date));

    // Adjust subsequent calendars to display consecutive months
    if (index > 0) {
        let newMonthDate = new Date(survey_date);
        newMonthDate.setMonth(newMonthDate.getMonth() + index); // Increment month for each subsequent calendar
        calendar.value(newMonthDate);
    }

    // Set specific startDate and endDate for highlighting
    calendar.options.startDate = new Date(early_date); // Replace with context-specific early_date
    calendar.options.endDate = new Date(late_date); // Replace with context-specific late_date
    calendar.refresh(); // Refresh the calendar to apply changes
});

// Ensure calendars are properly displayed on page load
window.addEventListener('DOMContentLoaded', () => {
    calendars.forEach(calendar => {
        calendar.show(); // Ensure each calendar is rendered
    });
});

/* Form validation and event handling */
const all_empty = () => {
    let is_empty = true;
    $("input[type=number]").each((i, e) => {
        if ($(e).val() !== '') {
            is_empty = false;
        }
    });
    return is_empty;
};

const validate_form = () => {
    if (calendar_enabled) {
        return true;
    }
    const msg = "Please fill out all token fields before changing pages.";
    let alerted = false;
    $("input[type=number]").each((i, e) => {
        if (!alerted && $(e).val() === "") {
            alerted = true;
            bulmaToast.toast({
                message: msg,
                position: "center",
                duration: 10000,
                dismissible: true,
                pauseOnHover: true,
                closeOnClick: true,
                opacity: .8,
                type: "is-danger"
            });
            $(e).focus();
            e.reportValidity();
        }
    });
    return !alerted;
};

const submit = (index) => {
    if (all_empty()) {
        $("#next_index").val(index);
        window.location.replace(`/calendar/${index}`);
    } else if (validate_form()) {
        $("#next_index").val(index);
        $("#myForm").submit();
    }
};

// Populate input fields if user tokens are available
if (Object.keys(user_tokens).length > 0) {
    $.each(user_tokens, (row, token_rates) => {
        $.each(token_rates, (rate, token) => {
            $(`#${row}-${rate}`).val(token);
        });
    });
}

$('input[type="number"]').each((_, e) => {
    e = $(e);
    if (validate(e.val())) {
        convex_handle(e);
    }
});
