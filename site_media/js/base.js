// General Tooltip function
function tooltip(targetnode, message, position, arrow){

    $(targetnode).qtip({
      content: message,
      position: {
         corner: {
            target: position,
            tooltip: arrow
         }
      },
      style: {
         name: 'cream',
         color: '#685D40',
         padding: '7px 13px',
         width: {
            max: 350,
            min: 0
         },
         border: {
            width: 3,
            radius: 3
         },
         tip: true
      }
    })
}
