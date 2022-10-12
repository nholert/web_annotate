
const pick_one = ()=>{
    $("#waiting-text").text(`Tab-${col} Row-${row}`)
    $("#row").css("display","block")
    let early_amount = early_tokens * early_rate/100
    let late_amount = late_tokens * late_rate/100
    $("#early-result").text(`$${early_amount.toFixed(2)}`)
    $("#late-result").text(`$${late_amount.toFixed(2)}`)
    $("#early-final-result").text(`$${(early_amount + 5).toFixed(2)}`)
    $("#late-final-result").text(`$${(late_amount + 5).toFixed(2)}`)
}


setTimeout(pick_one,850)