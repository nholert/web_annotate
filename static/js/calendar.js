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

function formatDateToString(date) {
    // Get the year, month, and day from the local date
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are zero-indexed
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

const earlyDateStr = formatDateToString(new Date(early_date));
const lateDateStr = formatDateToString(new Date(late_date));


/* Calendar */
// Initialize all input of date type.
const options = {
    showHeader: false,
    showClearButton: false,
    showTodayButton: false,
    isRange: false, // Disable range selection to highlight only specific dates
    enableMonthSwitch: false,
    enableYearSwitch: false,
    displayMode: "inline",
    type: 'date',
    date: new Date(late_date),  // Set default display date
    startDate: new Date(early_date), // Optional: for validation purposes
    surveyDate: new Date(survey_date), // Optional: if you need it for other logic
    highlightedDates: [earlyDateStr, lateDateStr] // Highlight only early_date and late_date
};

const calendars = bulmaCalendar.attach('[type="date"]', options);

if (options.startDate.getMonth()== options.surveyDate.getMonth()){
    //Starting the calendar on the survey date
    $(".datepicker-nav-next","#second-calendar").click()
    $(".datepicker-nav-next","#third-calendar").click().click()
    $(".datepicker-nav-next","#fourth-calendar").click().click().click()
    $(".datepicker-nav-next","#fifth-calendar").click().click().click().click()
}else if(options.startDate.getMonth() > options.surveyDate.getMonth()){
    // if the starting date is (one month) after the survey date, this ensures the month of the survey date is still displayed 
    $(".datepicker-nav-previous","#first-calendar").click()
    $(".datepicker-nav-next","#second-calendar")
    $(".datepicker-nav-next","#third-calendar").click()
    $(".datepicker-nav-next","#fourth-calendar").click().click()
    $(".datepicker-nav-next","#fifth-calendar").click().click().click()
}
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
