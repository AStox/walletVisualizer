const validateEthereumAddress = () => {
  try {
    const address = web3.utils.toChecksumAddress(rawInput);
  } catch (e) {
    return "invalid ethereum address";
  }
  return undefined;
};

export default validateEthereumAddress;
