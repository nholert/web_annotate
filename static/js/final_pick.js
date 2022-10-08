
const pick_one = ()=>{
    $("#waiting-text").text(`Tab-${col} Row-${row}`)
    $("#row").css("display","block")
    $("#early-result").text(`$${(early_tokens * early_rate/100).toFixed(2)}`)
    $("#late-result").text(`$${(late_tokens * late_rate/100).toFixed(2)}`)
}


setTimeout(pick_one,850)