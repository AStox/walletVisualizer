import { map } from "lodash"
import React from "react"
import { Line } from "recharts"

const LineFactory = (transactions, showUSD, chooseColor) => {
    console.log("jhbsdfjbdsk")
    // console.log(() => chooseColor())
    if (!transactions) return null
    let index = 0
    const colors = [
        "#C6920C",
        "#1DB6D4",
        '#E25635',
        "#08A984",
        "#A959F1"
      ];
    return (
            map(transactions[transactions.length - 1]["balances"], (_, key) => {
                index += 1
                console.log(colors[index % colors.length])
                return (
                    <Line
                        key={key}
                        type="monotone"
                        dataKey={showUSD ? `balancesUSD.${key}` : `balances.${key}`}
                        stroke={colors[index % colors.length]}
                        strokeWidth="3"
                    />
                )
            })
    )
  }

  export default LineFactory