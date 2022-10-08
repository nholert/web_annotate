
const pick_one = ()=>{
    $("#waiting-text").text(`Tab-${col} Row-${row}`)
    $("#row").css("display","block")
    $(".early-date").each((i,e)=>{
        $(e).text(early_date)
    })
    $(".late-date").each((i,e)=>{
        $(e).text(late_date)
    })
    $(".early-rate").each((i,e)=>{
        $(e).text(early_rate)
    })
    $(".late-rate").each((i,e)=>{
        $(e).text(late_rate)
    })
    $("#input-early").val(early_tokens)
    $("#input-late").val(late_tokens)
    $("#early-result").text(`${(early_tokens * early_rate/100).toFixed(2)}`)
    $("#late-result").text(`${(late_tokens * late_rate/100).toFixed(2)}`)
}


setTimeout(pick_one,1000)