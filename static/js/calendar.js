const validate = (value)=>{
    return value!="" && 0 <= value && value <= 50
}
const round = (value)=>{
    if (value < 0){
        return 0
    }else if (value > 50){
        return 50
    }else{
        return value
    }
}

const convex_combination = (self,target)=>{
    target.val(50-self.val(round(self.val())).val())

}
const convex_handle = (self)=>{
    self = $(self)
    target = $(`#${self.attr('target')}`)
    convex_combination(self,target)
    let self_id = self.attr('id')
    let target_id = target.attr('id')
    let self_rate = Number(self_id.split('-')[1])/100
    let target_rate = Number(target_id.split('-')[1])/100

    $(`#${self_id}-result`).text(`\$${(self_rate * self.val()).toFixed(2)}`)
    $(`#${target_id}-result`).text(`\$${(target_rate * target.val()).toFixed(2)}`)
}



/* Calendar */
// Initialize all input of date type.
const options = {
    showHeader: false,
    showClearButton: false,
    showTodayButton: false,
    isRange: true,
    enableMonthSwitch: false,
    enableYearSwitch: false,
    displayMode: "inline",
    type: 'date',
    endDate:  new Date(late_date),
    startDate: new Date(early_date),
    date: new Date(late_date),
    surveyDate: new Date(survey_date)
};


// Attach and configure each calendar instance
const calendars = bulmaCalendar.attach('[type="date"]', options);

// Set all calendars to display starting at the survey date
calendars.forEach((calendar, index) => {
    // Set the initial display to start at the survey date
    calendar.options.date = new Date(survey_date);
    calendar.value(new Date(survey_date));

    // Shift each calendar to show consecutive months after the survey date
    if (index > 0) {
        for (let i = 0; i < index; i++) {
            calendar.datePickerElements.navigation.nextButton.click();
        }
    }

    // Set specific startDate and endDate for highlighting unique dates for each tab
    calendar.options.startDate = new Date(early_date); // Replace with tab-specific early_date
    calendar.options.endDate = new Date(late_date); // Replace with tab-specific late_date
    calendar.refresh(); // Apply changes and refresh the calendar display
});

// Ensure calendars are displayed on page load
window.addEventListener('DOMContentLoaded', () => {
    calendars.forEach(calendar => {
        calendar.show(); // Ensure calendars render on page load
    });
});
/*
$(".datepicker-nav-next").each((i,e)=>{
    $(e).css('cursor','auto').css('z-index','-1')
});
$(".datepicker-nav-previous").each((i,e)=>{
    $(e).css('cursor','auto').css('z-index','-1')
});
*/

const all_empty = ()=>{
    var is_empty = true
    $("input[type=number]").each((i,e)=>{
        if ($(e).val()!=''){
            is_empty = false
        }
    })
    return is_empty
}
const validate_form = ()=>{
    if (calendar_enabled){
        return true
    }
    const msg = "Please fill out all token fields before changing pages."
    let alerted = false
    $("input[type=number]").each((i,e)=>{
        if (!alerted && $(e).val()==""){
            alerted = true
            bulmaToast.toast({ 
                message: msg,
                position: "center",
                duration: 10000,
                dismissible: true,
                pauseOnHover: true,
                closeOnClick: true,
                opacity: .8,
                type: "is-danger"
            })
            $(e).focus()
            e.reportValidity()
        }
    })
    return !alerted
}

const submit = (index)=>{
    if (all_empty()){
        $("#next_index").val(index);
        window.location.replace(`/calendar/${index}`);   
    }else if (validate_form()){
        $("#next_index").val(index);
        $("#myForm").submit();
    }
}

if (Object.keys(user_tokens).length > 0){
    //user_tokens is the data we need to populate the page.
    $.each(user_tokens,(row,token_rates)=>{
        $.each(token_rates,(rate,token)=>{
            $(`#${row}-${rate}`).val(token)
        })
    })
}

$('input[type="number"]').each((_,e)=>{
    e = $(e)
    if (validate(e.val())){
        convex_handle(e)
    }
})
