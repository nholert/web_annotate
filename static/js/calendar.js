const validate = (value)=>{
    return value!="" && 0 <= value && value <= 100
}
const round = (value)=>{
    if (value < 0){
        return 0
    }else if (value > 100){
        return 100
    }else{
        return value
    }
}

const convex_combination = (self,target)=>{
    target.val(100-self.val(round(self.val())).val())

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
$('input[type="number"]').each((_,e)=>{
    e = $(e)
    console.log(e.val())
    if (validate(e.val())){
        convex_handle(e)
    }
})


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
    minDate:  new Date(early_date),
    endDate:  new Date(late_date),
    startDate: new Date(early_date),
    date: new Date(late_date),
};
options['minDate'].addDays(1)
options['startDate'].addDays(1)
const calendars = bulmaCalendar.attach('[type="date"]', options);
$(".datepicker-nav-next","#nov").click()
$(".datepicker-nav-next","#dec").click().click()
$(".datepicker-nav-next","#jan").click().click().click()
$(".datepicker-nav-next","#feb").click().click().click().click()

$(".datepicker-nav-next").each((i,e)=>{
    $(e).css('cursor','auto').css('z-index','-1')
});
$(".datepicker-nav-previous").each((i,e)=>{
    $(e).css('cursor','auto').css('z-index','-1')
});