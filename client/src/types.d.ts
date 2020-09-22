type Transaction = {
  blockHash: string;
  blockNumber: number;
  confirmations: number;
  contractAddress: string;
  cumulativeGasUsed: number;
  from: string;
  gas: number;
  gasPrice: number;
  gasUsed: number;
  hash: string;
  input: string;
  isError: number;
  nonce: number;
  timeStamp: number;
  to: string;
  transactionIndex: number;
  txreceipt_status: number;
  value: number;
  values: Values;
  balances: Values;
};

type Values = {
  [key: string]: number;
};
